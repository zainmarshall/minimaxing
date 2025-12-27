import chess
from engine.evaluator import Bot

class Minimax:
    def __init__(self, bot: Bot, depth: int = 2):
        self.bot = bot
        self.depth = depth

    def evaluate(self, board: chess.Board) -> float:
        return self.bot.evaluate(board)

    def search(self, board: chess.Board, depth: int = None, alpha: float = float('-inf'), beta: float = float('inf'), maximizing: bool = True) -> float:
        if depth is None:
            depth = self.depth
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)
        if maximizing:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.search(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.search(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def best_move(self, board: chess.Board) -> tuple[str, float] | None:
        best_score = float('-inf')
        best_move = None
        for move in board.legal_moves:
            board.push(move)
            score = self.search(board, self.depth - 1, maximizing=False)
            board.pop()
            if score > best_score:
                best_score = score
                best_move = move
        if best_move:
            return best_move.uci(), best_score
        return None
