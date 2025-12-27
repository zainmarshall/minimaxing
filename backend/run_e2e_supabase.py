import time
import chess
from models import Rule, RuleSet, BotModel
from database import save_bot, get_bot, save_match, get_match_db, supabase
from match_store import create_match, get_match
from routes import api_play_match

# Simple material rule (same for both bots)
material_rule = Rule(
    name='Material',
    code=(
        "sum([len(board.pieces(p, chess.WHITE)) * v for p,v in [(chess.PAWN,1),(chess.KNIGHT,3),(chess.BISHOP,3),(chess.ROOK,5),(chess.QUEEN,9)]]) - "
        "sum([len(board.pieces(p, chess.BLACK)) * v for p,v in [(chess.PAWN,1),(chess.KNIGHT,3),(chess.BISHOP,3),(chess.ROOK,5),(chess.QUEEN,9)]])"
    ),
    weight=1.0,
)

ruleset = RuleSet(rules=[material_rule])

bot = BotModel(user_id='test_user', name='material-bot', rules=ruleset)
print('Saving bot to Supabase...')
bot_id = save_bot(bot)
print('Saved bot id:', bot_id)

# fetch bot back
try:
    fetched = get_bot(bot_id)
    print('Fetched bot name:', fetched.name)
except Exception as e:
    print('Failed to fetch bot:', e)

# create in-memory match using the bot's rules
match = create_match(fetched.rules, fetched.rules)
print('Created match id:', match.id)

# play the match
result = api_play_match(match.id, depth=2)
print('Play result:', result.result)
print('Moves:', len(result.fen_history)-1)

# persist match to supabase
print('Saving match to Supabase...')
save_match(match)
print('Saved match.')

# verify via supabase client
print('Verifying match row via Supabase...')
res = supabase.table('matches').select('*').eq('id', match.id).execute()
print('Supabase query returned rows:', len(res.data) if res.data is not None else 0)
if res.data:
    print('Match row id:', res.data[0].get('id'))
    print('Result in row:', res.data[0].get('result'))

print('Done')
