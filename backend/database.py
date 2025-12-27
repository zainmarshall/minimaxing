# This file can be used to manage database connections and queries

import os
from supabase import create_client, Client
from models import BotModel, Match

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if SUPABASE_URL and SUPABASE_ANON_KEY:
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
