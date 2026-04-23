# src/ui/app.py  — Updated with Supabase storage
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.groq_client import ask
from src.memory.conversation_store import save_message, load_conversation, get_or_create_session_id

st.set_page_config(page_title='AI Research Partner', page_icon='🧬', layout='wide')
st.title('🧬 AI Research Partner')

# Get or create a session ID for this user
session_id = get_or_create_session_id()

# Load conversation history from database (runs once on page load)
if 'messages' not in st.session_state:
    st.session_state.messages = load_conversation(session_id)

# Show all messages
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# Handle new user input
if prompt := st.chat_input('Ask your research question...'):
    # Save user message to database
    save_message(session_id, 'user', prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    with st.chat_message('user'):
        st.markdown(prompt)

    with st.chat_message('assistant'):
        with st.spinner('Thinking...'):
            system = '''You are an expert AI research partner for PhD-level life science researchers.
Give mechanistic, in-depth answers. Reference specific studies. Flag uncertainty explicitly.
Do not give overview answers. The researcher already knows the basics.'''

            response = ask(st.session_state.messages, system_prompt=system)

        st.markdown(response)

    # Save AI response to database
    save_message(session_id, 'assistant', response)
    st.session_state.messages.append({'role': 'assistant', 'content': response})
