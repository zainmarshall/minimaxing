import chess

class ChessGame:
    def __init__(self, fen: str = None):
        """Initialize the chess board. If FEN is provided, load that position."""
        self.board = chess.Board(fen) if fen else chess.Board()

    def get_fen(self) -> str:
        """Return the current board state as a FEN string."""
        return self.board.fen()

    def make_move(self, move_uci: str) -> bool:
        """Attempt to make a move in UCI format. Returns True if move is legal and made."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except Exception:
            return False

    def is_game_over(self) -> bool:
        """Check if the game is over (checkmate, stalemate, etc)."""
        return self.board.is_game_over()

    def result(self) -> str:
        """Return the result string if the game is over, else None."""
        if self.board.is_game_over():
            return self.board.result()
        return None

    def get_pgn(self) -> str:
        """Return the game in PGN format."""
        try:
            import chess.pgn
            game = chess.pgn.Game.from_board(self.board)
            return str(game)
        except Exception:
            # Fallback: return UCI move list
            return ' '.join([m.uci() for m in self.board.move_stack])
