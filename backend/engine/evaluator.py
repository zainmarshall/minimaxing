import chess
from typing import List, Dict, Optional
from . import helpers


class Evaluator:
    """
    Evaluator that supports both simple expression rules and full-script bots.
    If a bot version contains a `script` entry, the script is executed (unsafely)
    and its `evaluate(board)` function (or expression) is used as the board score.
    Otherwise, legacy `code` expressions with `weight` are used.
    """
    def __init__(self, rules: List[Dict]):
        self.rules = rules or []
        self.compiled_rules = []
        self.script_callable = None

        # Detect script-style rules first
        if len(self.rules) > 0 and isinstance(self.rules[0], dict) and "script" in self.rules[0]:
            src = self.rules[0]["script"]
            namespace: dict = {"chess": chess, "helpers": helpers}
            # Provide short helpers directly
            for name in dir(helpers):
                if not name.startswith("_"):
                    namespace[name] = getattr(helpers, name)

            try:
                exec(src, namespace)
            except Exception:
                # Compilation errors will be raised at evaluation time or earlier in upload endpoints
                self.script_callable = None
                return

            # Preferred: evaluate(board) function
            if "evaluate" in namespace and callable(namespace["evaluate"]):
                self.script_callable = namespace["evaluate"]
            else:
                # No evaluate found; attempt to compile as single expression
                try:
                    expr = compile(src, "<string>", "eval")
                    def _expr_eval(board: chess.Board):
                        return eval(expr, {"chess": chess, **{k: getattr(helpers, k) for k in dir(helpers) if not k.startswith("_")}}, {"board": board})
                    self.script_callable = _expr_eval
                except Exception:
                    self.script_callable = None

        else:
            # Legacy rule list: compile expression rules with weights
            for rule in self.rules:
                try:
                    code_obj = compile(rule["code"], "<string>", "eval")
                    weight = rule.get("weight", 1.0)
                    self.compiled_rules.append({"code": code_obj, "weight": weight})
                except Exception:
                    # skip invalid rules
                    pass

    def evaluate(self, board: chess.Board) -> float:
        if self.script_callable:
            try:
                # Call script-provided evaluator directly
                return float(self.script_callable(board))
            except Exception:
                return 0.0

        # Legacy evaluation path
        score = 0.0
        globals_dict = {"chess": chess}
        # inject helpers as locals to make them readily available for expressions
        locals_dict = {"board": board}
        for name in dir(helpers):
            if not name.startswith("_"):
                locals_dict[name] = getattr(helpers, name)

        for rule in self.compiled_rules:
            try:
                result = eval(rule["code"], globals_dict, locals_dict)
                score += float(result) * rule["weight"]
            except Exception:
                pass

        return score
