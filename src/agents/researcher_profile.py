# src/agents/researcher_profile.py
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def save_profile(session_id: str, profile: dict):
    '''Save or update researcher profile'''
    # Check if profile already exists
    existing = supabase.table('researcher_profiles') \
        .select('id') \
        .eq('session_id', session_id) \
        .execute()

    if existing.data:
        # Update existing profile
        supabase.table('researcher_profiles') \
            .update(profile) \
            .eq('session_id', session_id) \
            .execute()
    else:
        # Create new profile
        profile['session_id'] = session_id
        supabase.table('researcher_profiles').insert(profile).execute()

def load_profile(session_id: str) -> dict:
    '''Load researcher profile — returns empty dict if not found'''
    result = supabase.table('researcher_profiles') \
        .select('*') \
        .eq('session_id', session_id) \
        .execute()
    return result.data[0] if result.data else {}

def build_system_prompt(profile: dict) -> str:
    '''Build a PhD-calibrated system prompt from the researcher's profile'''

    level = profile.get('academic_level', 'researcher')
    domain = profile.get('research_domain', 'life science')
    project = profile.get('current_project', '')

    base = f'''You are an expert AI research thinking partner for a {level} in {domain}.

DEPTH CALIBRATION — CRITICAL:
This researcher has deep domain expertise. Do NOT give overview or introductory answers.
Assume they know the basics. Go straight to mechanistic depth, conflicting evidence, and
current methodological debates in the field.

REASONING STANDARDS:
- Always state the evidence quality: is this from a single study, meta-analysis, or consensus?
- When literature is conflicting, present both sides with the reasons they might differ
- Flag your own uncertainty explicitly: 'The evidence here is limited because...'
- Ask a pointed follow-up question at the end that challenges the researcher to think deeper

NEVER:
- Give Wikipedia-style overviews
- Assert something you cannot attribute to a study or established mechanism
- Agree with the researcher just to be agreeable — push back when their reasoning has gaps
'''

    if project:
        base += f'\nCurrent project context: {project}\n'
        base += 'Connect all answers to this project context when relevant.'

    return base
