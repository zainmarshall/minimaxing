from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List
from ..database import get_supabase_client
from ..security.validator import SecurityValidator
import chess
from typing import Optional
import hashlib
import json

router = APIRouter()
validator = SecurityValidator()

class Rule(BaseModel):
    name: str
    code: str
    weight: float

class BotVersionCreate(BaseModel):
    bot_id: str
    rules: List[Rule]
    search_depth: int

@router.post("/versions")
async def create_version(version_data: BotVersionCreate):
    # Validate each rule
    for rule in version_data.rules:
        if not validator.validate(rule.code):
            raise HTTPException(status_code=400, detail=f"Invalid or unsafe code in rule: {rule.name}")

    # Calculate hash of rules for immutability check/reference
    rules_json = [r.dict() for r in version_data.rules]
    rules_str = json.dumps(rules_json, sort_keys=True)
    rules_hash = hashlib.sha256(rules_str.encode()).hexdigest()

    # Insert into Supabase
    supabase = get_supabase_client()
    result = supabase.table("bot_versions").insert({
        "bot_id": version_data.bot_id,
        "rules_json": rules_json,
        "rules_hash": rules_hash,
        "search_depth": version_data.search_depth
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create bot version")

    version_id = result.data[0]["id"]
    
    # Optionally update the bot's active_version_id
    supabase.table("bots").update({"active_version_id": version_id}).eq("id", version_data.bot_id).execute()

    return result.data[0]


@router.post("/upload")
async def upload_bot_file(bot_id: str, file: UploadFile = File(...), search_depth: int = 3):
    """Accept a JSON file upload containing a bot version (rules).

    The uploaded JSON may contain either `rules` or `rules_json` as the array of rule objects.
    """
    content = await file.read()
    try:
        payload = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON")

    # Accept either `rules` or `rules_json`
    rules_input = payload.get("rules") or payload.get("rules_json")
    if not rules_input or not isinstance(rules_input, list):
        raise HTTPException(status_code=400, detail="JSON must contain a top-level 'rules' array")

    # Normalize into Rule structures and validate code
    normalized = []
    for r in rules_input:
        if not isinstance(r, dict) or "code" not in r or "weight" not in r:
            raise HTTPException(status_code=400, detail="Each rule must be an object with 'code' and 'weight'")
        name = r.get("name", "unnamed")
        code = r["code"]
        weight = r["weight"]

        if not validator.validate(code):
            raise HTTPException(status_code=400, detail=f"Invalid or unsafe code in rule: {name}")

        normalized.append({"name": name, "code": code, "weight": weight})

    # Calculate hash and insert similar to create_version
    rules_str = json.dumps(normalized, sort_keys=True)
    rules_hash = hashlib.sha256(rules_str.encode()).hexdigest()

    supabase = get_supabase_client()
    result = supabase.table("bot_versions").insert({
        "bot_id": bot_id,
        "rules_json": normalized,
        "rules_hash": rules_hash,
        "search_depth": search_depth
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create bot version from uploaded file")

    version_id = result.data[0]["id"]
    supabase.table("bots").update({"active_version_id": version_id}).eq("id", bot_id).execute()

    return result.data[0]


class ScriptUpload(BaseModel):
    bot_id: str
    code: str
    search_depth: Optional[int] = 3


@router.post("/upload-script")
async def upload_script(data: ScriptUpload):
    """Upload a user script (unsafe) and store it in `rules_json` as a script entry.

    NOTE: This endpoint intentionally does not validate or sandbox code. Use only in trusted/dev environments.
    """
    supabase = get_supabase_client()

    rules_json = [{"script": data.code}]
    rules_str = json.dumps(rules_json, sort_keys=True)
    rules_hash = hashlib.sha256(rules_str.encode()).hexdigest()

    result = supabase.table("bot_versions").insert({
        "bot_id": data.bot_id,
        "rules_json": rules_json,
        "rules_hash": rules_hash,
        "search_depth": data.search_depth or 3
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create bot version from script upload")

    version_id = result.data[0]["id"]
    supabase.table("bots").update({"active_version_id": version_id}).eq("id", data.bot_id).execute()

    return result.data[0]


class EvalBatchRequest(BaseModel):
    bot_version: str
    fens: List[str]


@router.post("/eval_batch")
async def eval_batch(req: EvalBatchRequest):
    """Evaluate a bot script on a batch of FEN strings and return scores.

    This executes user-provided code unsafely in-process. Only use in dev/trusted environments.
    The script must define a function `evaluate(board)` that returns a numeric score.
    """
    supabase = get_supabase_client()
    res = supabase.table("bot_versions").select("*").eq("id", req.bot_version).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Bot version not found")

    bot_data = res.data
    code = None
    try:
        rjson = bot_data.get("rules_json")
        if isinstance(rjson, list) and len(rjson) > 0 and isinstance(rjson[0], dict) and "script" in rjson[0]:
            code = rjson[0]["script"]
    except Exception:
        code = None

    if not code:
        raise HTTPException(status_code=400, detail="No script found for this bot version")

    # Unsafe execution environment (intentionally permissive per request)
    # Inject helpers into script namespace for convenience
    from ..engine import helpers as helpers_module
    namespace: dict = {"chess": chess, "helpers": helpers_module}
    for name in dir(helpers_module):
        if not name.startswith("_"):
            namespace[name] = getattr(helpers_module, name)
    try:
        exec(code, namespace)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error compiling script: {e}")

    if "evaluate" not in namespace or not callable(namespace["evaluate"]):
        raise HTTPException(status_code=400, detail="Script must define a callable 'evaluate(board)' function")

    evaluate = namespace["evaluate"]
    scores = []
    for fen in req.fens:
        try:
            b = chess.Board(fen)
            score = evaluate(b)
            scores.append(score)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluating FEN '{fen}': {e}")

    return {"scores": scores}

@router.get("/{bot_id}/versions")
async def get_bot_versions(bot_id: str):
    supabase = get_supabase_client()
    result = supabase.table("bot_versions").select("*").eq("bot_id", bot_id).execute()
    return result.data


@router.get("/versions/{version_id}")
async def get_version(version_id: str):
    supabase = get_supabase_client()
    result = supabase.table("bot_versions").select("*").eq("id", version_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Version not found")
    return result.data


@router.delete("/versions/{version_id}")
async def delete_version(version_id: str):
    supabase = get_supabase_client()
    # Check for matches referencing this version
    m = supabase.table("matches").select("id").or_(f"bot_a_version.eq.{version_id},bot_b_version.eq.{version_id}").execute()
    if m.data and len(m.data) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete version: it is referenced by existing matches")

    # Safe to remove the version
    res = supabase.table("bot_versions").delete().eq("id", version_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail="Failed to delete version")
    return {"deleted": True}


class VersionUpdate(BaseModel):
    rules: List[dict]
    search_depth: Optional[int] = None


@router.patch("/versions/{version_id}")
async def update_version(version_id: str, data: VersionUpdate):
    """Update rules/search depth for an existing version.

    This will refuse to update a version that is already referenced by matches to preserve reproducibility.
    """
    supabase = get_supabase_client()
    # Check references
    m = supabase.table("matches").select("id").or_(f"bot_a_version.eq.{version_id},bot_b_version.eq.{version_id}").execute()
    if m.data and len(m.data) > 0:
        raise HTTPException(status_code=400, detail="Cannot modify version: it is referenced by existing matches. Clone instead.")

    rules_json = data.rules
    rules_str = json.dumps(rules_json, sort_keys=True)
    rules_hash = hashlib.sha256(rules_str.encode()).hexdigest()

    update_payload = {"rules_json": rules_json, "rules_hash": rules_hash}
    if data.search_depth is not None:
        update_payload["search_depth"] = data.search_depth

    res = supabase.table("bot_versions").update(update_payload).eq("id", version_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail="Failed to update version")
    return res.data[0]


class CloneVersionRequest(BaseModel):
    bot_id: str
    search_depth: Optional[int] = None


@router.post("/versions/{version_id}/clone")
async def clone_version(version_id: str, data: CloneVersionRequest):
    supabase = get_supabase_client()
    res = supabase.table("bot_versions").select("*").eq("id", version_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Source version not found")

    src = res.data
    rules_json = src.get("rules_json")
    search_depth = data.search_depth if data.search_depth is not None else src.get("search_depth", 3)

    rules_str = json.dumps(rules_json, sort_keys=True)
    rules_hash = hashlib.sha256(rules_str.encode()).hexdigest()

    inserted = supabase.table("bot_versions").insert({
        "bot_id": data.bot_id,
        "rules_json": rules_json,
        "rules_hash": rules_hash,
        "search_depth": search_depth
    }).execute()

    if not inserted.data:
        raise HTTPException(status_code=500, detail="Failed to clone version")

    new_id = inserted.data[0]["id"]
    supabase.table("bots").update({"active_version_id": new_id}).eq("id", data.bot_id).execute()
    return inserted.data[0]


@router.delete("/{bot_id}")
async def delete_bot(bot_id: str):
    supabase = get_supabase_client()
    # Ensure none of the bot's versions are referenced by matches
    versions = supabase.table("bot_versions").select("id").eq("bot_id", bot_id).execute()
    if versions.data:
        for v in versions.data:
            vid = v.get("id")
            m = supabase.table("matches").select("id").or_(f"bot_a_version.eq.{vid},bot_b_version.eq.{vid}").execute()
            if m.data and len(m.data) > 0:
                raise HTTPException(status_code=400, detail=f"Cannot delete bot: version {vid} is referenced by matches")

    # Safe to delete versions and bot
    supabase.table("bot_versions").delete().eq("bot_id", bot_id).execute()
    res = supabase.table("bots").delete().eq("id", bot_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail="Failed to delete bot")
    return {"deleted": True}
