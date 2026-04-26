# src/memory/conversation_store.py
import os
import uuid

try:
    import streamlit as st
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

from supabase import create_client
supabase = create_client(url, key)


def save_message(session_id: str, role: str, content: str):
    '''Save one message to Supabase — fails silently so app never crashes'''
    try:
        supabase.table('conversations').insert({
            'session_id': session_id,
            'role': role,
            'content': content
        }).execute()
    except Exception as e:
        print(f'Supabase save failed (non-critical): {e}')


def load_conversation(session_id: str) -> list:
    '''Load all messages for a session — returns empty list on any failure'''
    try:
        result = supabase.table('conversations') \
            .select('role, content, created_at') \
            .eq('session_id', session_id) \
            .order('created_at') \
            .execute()
        return [
            {'role': r['role'], 'content': r['content']}
            for r in result.data
        ]
    except Exception as e:
        print(f'Supabase load failed (non-critical): {e}')
        return []


def get_or_create_session_id() -> str:
    '''
    Generate a unique session ID per browser session.
    Stored in st.session_state so it survives Streamlit reruns.
    '''
    import streamlit as st
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id