import os
from supabase import create_client, Client

SUPABASE_URL = "https://qqdhjllycrrcivgxjeoy.supabase.co"
SUPABASE_KEY = "sb_secret_YJirgg9ce0wMBp0MhtOWyw_71nsGpEy"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> Client:
    return supabase
