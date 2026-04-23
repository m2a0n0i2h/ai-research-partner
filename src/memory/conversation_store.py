# src/memory/conversation_store.py
import os
import uuid
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Connect to your Supabase database
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def save_message(session_id: str, role: str, content: str):
    '''Save one message to the database'''
    supabase.table('conversations').insert({
        'session_id': session_id,
        'role': role,
        'content': content
    }).execute()

def load_conversation(session_id: str) -> list:
    '''Load all messages for a session, oldest first'''
    result = supabase.table('conversations') \
        .select('role, content, created_at') \
        .eq('session_id', session_id) \
        .order('created_at') \
        .execute()

    # Return just the role and content, not the timestamp
    return [{'role': r['role'], 'content': r['content']} for r in result.data]

def get_or_create_session_id() -> str:
    '''Create a unique session ID for this browser session'''
    # For now, use a fixed ID per device — will improve with auth later
    return 'session_001'
