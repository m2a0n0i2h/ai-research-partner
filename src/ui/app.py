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
# Add to src/ui/app.py — SIDEBAR PROFILE SECTION
# (insert this after session_id = get_or_create_session_id())

from src.agents.researcher_profile import save_profile, load_profile, build_system_prompt

# Load profile from database
if 'profile' not in st.session_state:
    st.session_state.profile = load_profile(session_id)

# Sidebar for profile setup
with st.sidebar:
    st.header('Your Research Profile')

    name = st.text_input('Name', value=st.session_state.profile.get('name', ''))

    level = st.selectbox('Academic Level',
        ['phd_student', 'postdoc', 'professor', 'industry_researcher'],
        index=0
    )

    domain = st.text_input('Research Domain',
        value=st.session_state.profile.get('research_domain', ''),
        placeholder='e.g., molecular biology, genomics'
    )

    project = st.text_area('Current Project (brief description)',
        value=st.session_state.profile.get('current_project', ''),
        height=100
    )

    if st.button('Save Profile'):
        profile_data = {
            'name': name, 'academic_level': level,
            'research_domain': domain, 'current_project': project
        }
        save_profile(session_id, profile_data)
        st.session_state.profile = profile_data
        st.success('Profile saved!')

# Build the system prompt from profile
system_prompt = build_system_prompt(st.session_state.profile)

# Now use system_prompt instead of the hardcoded string in your ask() call

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
