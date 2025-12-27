# This file can be used to define API endpoints related to chess logic, matchmaking, etc.

from fastapi import APIRouter, HTTPException
from models import RuleSet, Match, MatchResult, MoveRequest, MoveResponse, BotModel
from database import save_bot, get_bot
from minimax import Minimax
from engine.evaluator import Bot
from board import ChessGame
import chess

router = APIRouter()

@router.get("/status")
def get_status():
    return {"status": "Backend is running"}

@router.post("/api/move", response_model=MoveResponse)
def calculate_move(request: MoveRequest):
    try:
        board = chess.Board(request.fen)
        bot = Bot(request.rules.rules)
        minimax = Minimax(bot, request.depth)
        result = minimax.best_move(board)
        if result:
            move, score = result
            return MoveResponse(move=move, score=score)
        else:
            raise HTTPException(status_code=400, detail="No legal moves")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/bot/submit")
def submit_ruleset(ruleset: RuleSet):
    # For now, just validate
    try:
        Bot(ruleset.rules)
        return {"status": "valid"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Placeholder for bot management
@router.post("/api/bot/create")
def create_bot(bot: BotModel):
    try:
        bot_id = save_bot(bot)
        bot.id = bot_id
        return bot
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/api/bot/{bot_id}")
def get_bot_endpoint(bot_id: str):
    try:
        return get_bot(bot_id)
    except ValueError:
        raise HTTPException(404, "Bot not found")

# Endpoint to create a match with two rulesets
@router.post("/api/match/create", response_model=Match)
def api_create_match(white_rules: RuleSet, black_rules: RuleSet):
    from match_store import create_match
    match = create_match(white_rules, black_rules)
    return match

# Endpoint to play out a match and return the result
@router.post("/api/match/{match_id}/play", response_model=MatchResult)
def api_play_match(match_id: str, depth: int = 2):
    from match_store import get_match, save_match_result

    match = get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    try:
        white_bot = Bot(match.white_rules.rules)
        black_bot = Bot(match.black_rules.rules)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    minimax_white = Minimax(white_bot, depth)
    minimax_black = Minimax(black_bot, depth)
    game = ChessGame()
    fen_history = [game.get_fen()]
    turn = True  # True = white, False = black
    while not game.is_game_over():
        minimax = minimax_white if turn else minimax_black
        result = minimax.best_move(game.board)
        if result:
            move_uci, _ = result
            game.make_move(move_uci)
        else:
            break
        fen_history.append(game.get_fen())
        turn = not turn
    result_str = game.result()
    pgn = game.get_pgn()
    save_match_result(match_id, result_str, fen_history)
    return MatchResult(match_id=match_id, result=result_str, fen_history=fen_history, pgn=str(pgn))
@router.get("/api/match/{match_id}")
def get_match_endpoint(match_id: str):
    match = get_match(match_id)
    if not match:
        raise HTTPException(404, "Match not found")
    return match
