import chess
from .evaluator import Evaluator

class ChessEngine:
    """
    Chess engine using Negamax with alpha-beta pruning.
    """
    def __init__(self, evaluator: Evaluator, depth: int, repetition_penalty: float = 150.0):
        self.evaluator = evaluator
        self.depth = depth
        # Penalty (in same units as evaluator) subtracted from moves that lead to threefold repetition
        self.repetition_penalty = repetition_penalty

    def get_best_move(self, board: chess.Board) -> tuple[chess.Move, float, dict[str, float]]:
        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        move_evals = {}

        moves = list(board.legal_moves)
        moves.sort(key=lambda m: m.uci())

        for move in moves:
            board.push(move)
            score = -self.negamax(board, self.depth - 1, -beta, -alpha)
            # Penalize positions that are repeated (threefold repetition) to discourage draws by repetition
            try:
                if board.is_repetition():
                    score -= self.repetition_penalty
            except Exception:
                pass
            board.pop()
            
            move_evals[move.uci()] = score

            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if alpha >= beta:
                # To show a "tree" or all options, we don't break on the top level
                pass
        
        return best_move, best_score, move_evals

    def negamax(self, board: chess.Board, depth: int, alpha: float, beta: float) -> float:
        if depth == 0 or board.is_game_over():
            # Return evaluation from the perspective of the side to move
            score = self.evaluator.evaluate(board)
            return score if board.turn == chess.WHITE else -score

        max_score = float('-inf')
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: m.uci())

        for move in moves:
            board.push(move)
            score = -self.negamax(board, depth - 1, -beta, -alpha)
            # Penalize repetition at deeper search as well
            try:
                if board.is_repetition():
                    score -= self.repetition_penalty
            except Exception:
                pass
            board.pop()

            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return max_score
