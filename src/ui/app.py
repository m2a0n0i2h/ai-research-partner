# src/ui/app.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.api.groq_client import ask
from src.memory.conversation_store import save_message, load_conversation, get_or_create_session_id
from src.memory.vector_store import add_memory, build_memory_context

st.set_page_config(
    page_title='AI Research Partner',
    page_icon='🧬',
    layout='wide'
)

st.title('🧬 AI Research Partner')
st.caption('Your PhD-level research thinking partner')

# Session ID for this user
session_id = get_or_create_session_id()

# Load conversation from Supabase on first load
if 'messages' not in st.session_state:
    st.session_state.messages = load_conversation(session_id)

# Display all past messages
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# Handle new input
if prompt := st.chat_input('Ask your research question...'):

    # Save user message
    save_message(session_id, 'user', prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    with st.chat_message('user'):
        st.markdown(prompt)

    with st.chat_message('assistant'):
        with st.spinner('Thinking...'):

            # Get relevant memories
            memory_context = build_memory_context(prompt)

            # Build system prompt
            system = '''You are an expert AI research thinking partner for PhD-level life science researchers.

DEPTH CALIBRATION — CRITICAL:
This researcher has deep domain expertise. Do NOT give overview or introductory answers.
Assume they know the basics. Go straight to mechanistic depth, conflicting evidence,
and current methodological debates in the field.

REASONING STANDARDS:
- State the evidence quality: single study, meta-analysis, or consensus?
- When literature conflicts, present both sides with reasons they might differ
- Flag your own uncertainty explicitly
- End with a pointed question that challenges the researcher to think deeper

NEVER give Wikipedia-style overviews or assert something without attributing it.'''

            if memory_context:
                system += f'\n\n{memory_context}'

            response = ask(st.session_state.messages, system_prompt=system)

        st.markdown(response)

    # Save AI response
    save_message(session_id, 'assistant', response)
    st.session_state.messages.append({'role': 'assistant', 'content': response})

    # Store exchange as memory
    memory_text = f'User asked: {prompt[:200]}. Key response: {response[:300]}'
    add_memory(memory_text, category='CONVERSATION')