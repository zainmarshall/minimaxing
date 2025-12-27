"""This file manages Supabase connections and queries.

It will attempt to load environment variables from a `.env` file
if `python-dotenv` is installed. If no Supabase credentials are
present, it falls back to an in-memory placeholder.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv not installed or .env not present — continue
    pass

from supabase import create_client, Client
from models import BotModel, Match

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Prefer service key for privileged server operations when available
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
elif SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None  # Fallback to in-memory

# Bot operations
def save_bot(bot: BotModel) -> str:
    if supabase:
        data = bot.dict()
        data.pop('id', None)
        response = supabase.table('bots').insert(data).execute()
        return response.data[0]['id']
    else:
        # In-memory placeholder
        return "mock_id"

def get_bot(bot_id: str) -> BotModel:
    if supabase:
        response = supabase.table('bots').select('*').eq('id', bot_id).execute()
        if response.data:
            return BotModel(**response.data[0])
    raise ValueError("Bot not found")

# Match operations
def save_match(match: Match):
    if supabase:
        data = match.dict()
        supabase.table('matches').insert(data).execute()

def get_match_db(match_id: str) -> Match:
    if supabase:
        response = supabase.table('matches').select('*').eq('id', match_id).execute()
        if response.data:
            return Match(**response.data[0])
    raise ValueError("Match not found")
