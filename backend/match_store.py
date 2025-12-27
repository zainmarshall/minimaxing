import uuid
from models import Match, RuleSet

# In-memory match store (replace with DB in production)
matches = {}

def create_match(white_rules: RuleSet, black_rules: RuleSet) -> Match:
    match_id = str(uuid.uuid4())
    match = Match(id=match_id, white_rules=white_rules, black_rules=black_rules, fen_history=[])
    matches[match_id] = match
    return match

def get_match(match_id: str) -> Match:
    return matches.get(match_id)

def save_match_result(match_id: str, result: str, fen_history: list[str]):
    match = matches.get(match_id)
    if match:
        match.result = result
        match.fen_history = fen_history
