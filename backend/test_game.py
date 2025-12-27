import chess
from models import Rule, RuleSet
from routes import api_create_match, api_play_match

# Define simple material evaluation rule
material_rule = Rule(
    name='Material Advantage',
    code='''sum([len(board.pieces(p, chess.WHITE)) * v for p,v in [(chess.PAWN,1),(chess.KNIGHT,3),(chess.BISHOP,3),(chess.ROOK,5),(chess.QUEEN,9)]]) - sum([len(board.pieces(p, chess.BLACK)) * v for p,v in [(chess.PAWN,1),(chess.KNIGHT,3),(chess.BISHOP,3),(chess.ROOK,5),(chess.QUEEN,9)]])''',
    weight=1.0
)

white_rules = RuleSet(rules=[material_rule])
black_rules = RuleSet(rules=[material_rule])

# Create match
match = api_create_match(white_rules, black_rules)
print(f'Created match: {match.id}')

# Play match
result = api_play_match(match.id, depth=2)
print(f'Result: {result.result}')
print(f'Moves: {len(result.fen_history) - 1}')
print(f'PGN: {result.pgn}')