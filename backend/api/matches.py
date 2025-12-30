from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..database import get_supabase_client
from ..engine.chess_engine import ChessEngine
from ..engine.evaluator import Evaluator
import chess
import chess.pgn
import io

router = APIRouter()

class MatchRequest(BaseModel):
    bot_a_version: str
    bot_b_version: str

def run_match_task(match_id: str, bot_a_version: str, bot_b_version: str):
    supabase = get_supabase_client()
    
    # Update status to running
    supabase.table("match_queue").update({"status": "running"}).eq("id", match_id).execute()

    try:
        # Fetch bot versions
        res_a = supabase.table("bot_versions").select("*").eq("id", bot_a_version).single().execute()
        res_b = supabase.table("bot_versions").select("*").eq("id", bot_b_version).single().execute()
        
        bot_a_data = res_a.data
        bot_b_data = res_b.data

        # Initialize engines
        engine_a = ChessEngine(Evaluator(bot_a_data["rules_json"]), bot_a_data["search_depth"])
        engine_b = ChessEngine(Evaluator(bot_b_data["rules_json"]), bot_b_data["search_depth"])

        board = chess.Board()
        game = chess.pgn.Game()
        game.headers["White"] = f"Bot A ({bot_a_version})"
        game.headers["Black"] = f"Bot B ({bot_b_version})"
        node = game

        print(f"Starting match {match_id} between {bot_a_version} and {bot_b_version}")

        # Game loop
        move_count = 0
        search_metadata = []
        
        while not board.is_game_over():
            current_engine = engine_a if board.turn == chess.WHITE else engine_b
            # get_best_move now returns (move, score, metadata)
            move, score, metadata = current_engine.get_best_move(board)
            
            if move is None:
                print(f"Match {match_id}: Engine returned no move. Ending.")
                break
            
            # Store metadata for this move
            search_metadata.append({
                "move_idx": move_count,
                "turn": "white" if board.turn == chess.WHITE else "black",
                "eval": score,
                "top_moves": metadata
            })
            
            board.push(move)
            # Standard eval is from White's perspective
            eval_score = score if board.turn == chess.BLACK else -score
            node = node.add_main_variation(move)
            node.comment = f"eval: {eval_score:.2f}"
            
            move_count += 1
            if move_count % 10 == 0:
                print(f"Match {match_id}: {move_count} moves played... Sample Eval: {eval_score:.2f}")

        # Result determination
        result = board.result()
        winner = "draw"
        if result == "1-0": winner = "A"
        elif result == "0-1": winner = "B"

        termination = "checkmate"
        if board.is_stalemate():
            termination = "stalemate"
        elif board.is_insufficient_material():
            termination = "insufficient material"
        elif board.is_fifty_moves():
            termination = "fifty-move rule"
        elif board.can_claim_threefold_repetition() or board.is_repetition():
            termination = "threefold repetition"
        elif result == "1/2-1/2":
            termination = "draw"

        print(f"Match {match_id} finished. Result: {result} ({winner}), Reason: {termination}")

        # Update Supabase
        pgn_str = str(game)
        # Attempt to store search metadata if the schema supports it.
        try:
            supabase.table("matches").insert({
                "id": match_id,
                "bot_a_version": bot_a_version,
                "bot_b_version": bot_b_version,
                "winner": winner,
                "termination_reason": termination,
                "pgn": pgn_str,
                "search_metadata": search_metadata
            }).execute()
        except Exception as insert_err:
            # If the matches table does not have the `search_metadata` column, retry without it.
            msg = str(insert_err)
            if "search_metadata" in msg:
                print(f"Warning: 'search_metadata' column missing, retrying insert without it: {msg}")
                supabase.table("matches").insert({
                    "id": match_id,
                    "bot_a_version": bot_a_version,
                    "bot_b_version": bot_b_version,
                    "winner": winner,
                    "termination_reason": termination,
                    "pgn": pgn_str,
                }).execute()
            else:
                raise

        supabase.table("match_queue").update({"status": "completed"}).eq("id", match_id).execute()

    except Exception as e:
        import traceback
        supabase.table("match_queue").update({"status": "failed"}).eq("id", match_id).execute()
        print(f"Match {match_id} failed with error: {e}")
        traceback.print_exc()

@router.post("/trigger")
async def trigger_match(request: MatchRequest, background_tasks: BackgroundTasks):
    supabase = get_supabase_client()
    
    # Create entry in match_queue
    result = supabase.table("match_queue").insert({
        "bot_a_version": request.bot_a_version,
        "bot_b_version": request.bot_b_version,
        "status": "queued"
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to queue match")

    match_id = result.data[0]["id"]
    
    # Run match in background
    background_tasks.add_task(run_match_task, match_id, request.bot_a_version, request.bot_b_version)

    return {"match_id": match_id, "status": "queued"}
