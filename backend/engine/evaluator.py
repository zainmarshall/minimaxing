import chess
from core.security import validate_rule
from models import Rule

class Bot:
    def __init__(self, rules: list[Rule]):
        self.compiled_rules = []
        for rule in rules:
            is_valid, msg = validate_rule(rule.code)
            if not is_valid:
                raise ValueError(f"Invalid rule '{rule.name}': {msg}")
            compiled = compile(rule.code, '<string>', 'eval')
            self.compiled_rules.append((compiled, rule.weight))

    def evaluate(self, board: chess.Board) -> float:
        score = 0.0
        for compiled, weight in self.compiled_rules:
            try:
                value = eval(compiled, {"__builtins__": None}, {"board": board, "chess": chess})
                score += weight * value
            except Exception:
                # Ignore invalid evaluations for robustness
                pass
        return score