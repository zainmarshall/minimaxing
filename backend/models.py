from pydantic import BaseModel
from typing import List, Optional

class Rule(BaseModel):
    name: str
    code: str  # Python expression evaluating to a number
    weight: float

class RuleSet(BaseModel):
    rules: List[Rule]

class BotModel(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    rules: RuleSet
    elo: float = 1200

class Match(BaseModel):
    id: str
    white_rules: RuleSet
    black_rules: RuleSet
    fen_history: list[str] = []
    result: Optional[str] = None
    pgn: Optional[str] = None

class MatchResult(BaseModel):
    match_id: str
    result: str
    fen_history: list[str]
    pgn: str

class MoveRequest(BaseModel):
    fen: str
    rules: RuleSet
    depth: int = 2

class MoveResponse(BaseModel):
    move: str
    score: float
