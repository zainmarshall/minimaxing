import chess
from typing import List, Dict, Optional

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]


def fen(board: chess.Board) -> str:
    return board.fen()


def material(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    score = 0
    for pt, val in piece_values.items():
        score += (len(board.pieces(pt, color)) - len(board.pieces(pt, not color))) * val
    return score


def mobility(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        # mobility of side to move
        return len(list(board.legal_moves))
    # mobility for a particular color: generate moves by making a copy and forcing turn
    b = board.copy(stack=False)
    b.turn = color
    return len(list(b.legal_moves))


def piece_count(board: chess.Board, piece_type: int, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    return len(board.pieces(piece_type, color))


def king_attackers(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    king_sq = board.king(color)
    if king_sq is None:
        return 0
    return len(board.attackers(not color, king_sq))


def is_check(board: chess.Board) -> bool:
    return board.is_check()


def is_checkmate(board: chess.Board) -> bool:
    return board.is_checkmate()


def is_stalemate(board: chess.Board) -> bool:
    return board.is_stalemate()


def history_fens(board: chess.Board, n: Optional[int] = None) -> List[str]:
    # Reconstruct positions from the starting position by replaying the move stack
    b = chess.Board()
    fens = [b.fen()]
    for mv in board.move_stack:
        b.push(mv)
        fens.append(b.fen())
    if n is not None:
        return fens[-n:]
    return fens


def repetition_count(board: chess.Board) -> int:
    current = board.fen()
    fens = history_fens(board)
    return fens.count(current)


def last_move(board: chess.Board) -> Optional[str]:
    if not board.move_stack:
        return None
    return board.move_stack[-1].uci()


def center_control(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    score = 0
    for sq in CENTER_SQUARES:
        piece = board.piece_at(sq)
        if piece is not None and piece.color == color:
            score += 1
        # also count attacks
        if color == board.turn:
            if any(True for _ in board.attackers(color, sq)):
                score += 0
    return score


def bishop_pair_bonus(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    return 1 if len(board.pieces(chess.BISHOP, color)) >= 2 else 0


def pawn_structure(board: chess.Board, color: Optional[bool] = None) -> Dict[str, int]:
    if color is None:
        color = board.turn
    files = {f: 0 for f in range(8)}
    pawns = board.pieces(chess.PAWN, color)
    passed = 0
    isolated = 0
    doubled = 0
    for sq in pawns:
        file = chess.square_file(sq)
        files[file] += 1
    for file, cnt in files.items():
        if cnt > 1:
            doubled += cnt - 1
    for sq in pawns:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        # isolated
        adjacent = False
        for df in (-1, 1):
            nf = file + df
            if 0 <= nf < 8 and files[nf] > 0:
                adjacent = True
        if not adjacent:
            isolated += 1
        # passed pawn: no enemy pawns in front on same or adjacent files
        is_passed = True
        enemy_pawns = board.pieces(chess.PAWN, not color)
        for ep in enemy_pawns:
            ef = chess.square_file(ep)
            er = chess.square_rank(ep)
            if abs(ef - file) <= 1:
                if (color == chess.WHITE and er > rank) or (color == chess.BLACK and er < rank):
                    is_passed = False
                    break
        if is_passed:
            passed += 1
    return {"passed": passed, "isolated": isolated, "doubled": doubled}


def distance_to_promotion(board: chess.Board, square: int) -> int:
    piece = board.piece_at(square)
    if not piece or piece.piece_type != chess.PAWN:
        return 0
    rank = chess.square_rank(square)
    if piece.color == chess.WHITE:
        return 7 - rank
    return rank


def threatened_material_change(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    score = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if not p or p.color != color:
            continue
        attackers = board.attackers(not color, sq)
        if attackers and not board.attackers(color, sq):
            # piece attacked and not defended
            score -= piece_values.get(p.piece_type, 0)
    return score


def evaluate_side(board: chess.Board, color: Optional[bool] = None) -> int:
    if color is None:
        color = board.turn
    s = 0
    s += material(board, color)
    s += 10 * mobility(board, color)
    s += 30 * center_control(board, color)
    s += 50 * bishop_pair_bonus(board, color)
    ps = pawn_structure(board, color)
    s += 30 * ps.get("passed", 0)
    s -= 40 * ps.get("isolated", 0)
    return s
