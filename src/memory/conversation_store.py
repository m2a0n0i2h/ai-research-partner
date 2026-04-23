# src/memory/conversation_store.py
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def save_message(session_id: str, role: str, content: str):
    supabase.table('conversations').insert({
        'session_id': session_id,
        'role': role,
        'content': content
    }).execute()

def load_conversation(session_id: str) -> list:
    result = supabase.table('conversations') \
        .select('role, content, created_at') \
        .eq('session_id', session_id) \
        .order('created_at') \
        .execute()
    return [{'role': r['role'], 'content': r['content']} for r in result.data]

def get_or_create_session_id() -> str:
    return 'session_001'