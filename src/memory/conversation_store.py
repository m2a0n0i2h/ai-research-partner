# src/memory/conversation_store.py
import os
from supabase import create_client

try:
    import streamlit as st
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

def save_message(session_id: str, role: str, content: str):
    """Save one message to the database"""
    supabase.table('conversations').insert({
        'session_id': session_id,
        'role': role,
        'content': content
    }).execute()

def load_conversation(session_id: str) -> list:
    """Load all messages for a session, oldest first"""
    result = supabase.table('conversations') \
        .select('role, content, created_at') \
        .eq('session_id', session_id) \
        .order('created_at') \
        .execute()
    return [{'role': r['role'], 'content': r['content']} for r in result.data]

def get_or_create_session_id() -> str:
    """Return a fixed session ID for now — will improve with auth later"""
    return 'session_001'