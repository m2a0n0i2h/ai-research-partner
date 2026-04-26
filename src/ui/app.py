# src/ui/app.py
# Complete Phase 2 version
# Fixes: hallucination prevention, literature routing, Chroma cloud fix

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.api.groq_client import ask
from src.memory.conversation_store import save_message, load_conversation, get_or_create_session_id
from src.memory.vector_store import add_memory, build_memory_context
from src.agents.prior_work_mapper import map_prior_work

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='AI Research Partner',
    page_icon='🧬',
    layout='wide'
)

# ─────────────────────────────────────────────────────────────
# HELPER: DETECT LITERATURE SEARCH QUESTIONS
# ─────────────────────────────────────────────────────────────
def is_literature_question(text: str) -> bool:
    '''
    Detect if the user is asking for research papers or citations.
    These MUST go to Prior Work Mapper — never answered from AI memory.
    '''
    signals = [
        'research on', 'papers on', 'articles on', 'studies on',
        'literature on', 'published', 'give me papers', 'find papers',
        'search for papers', 'any research', 'any papers', 'any articles',
        'any studies', 'research article', 'journal article', 'show me papers',
        'what is known about', 'what has been done', 'existing work',
        'what research exists', 'cite', 'citation', 'reference', 'references',
        'who published', 'recent studies', 'recent papers', 'latest research',
        'give me a study', 'give me an article', 'give me a paper',
    ]
    text_lower = text.lower()
    return any(signal in text_lower for signal in signals)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title('🧬 AI Research Partner')
    st.caption('Built at IISER Mohali')
    st.divider()

    st.subheader('Your Research Profile')

    name = st.text_input('Name', placeholder='Your name')

    level = st.selectbox(
        'Academic Level',
        ['PhD Student', 'Postdoc', 'Professor', 'Industry Researcher', 'Masters Student']
    )

    domain = st.text_input(
        'Research Domain',
        placeholder='e.g. molecular biology, genomics, biochemistry'
    )

    project = st.text_area(
        'Current Project',
        placeholder='Brief description of what you are working on right now...',
        height=100
    )

    st.divider()
    st.caption('📌 For literature search — use the **Prior Work Mapper** tab.')
    st.caption('💬 For concepts and discussion — use the **Chat** tab.')
    st.divider()
    st.caption('v0.2 — Phase 2 Active')


# ─────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────
tab_chat, tab_research = st.tabs(['💬 Chat', '🔬 Prior Work Mapper'])


# ═════════════════════════════════════════════════════════════
# TAB 1: CHAT
# ═════════════════════════════════════════════════════════════
with tab_chat:
    st.header('Research Chat')
    st.caption('Discuss concepts, mechanisms, and ideas — memory persists across sessions')

    # Warning banner
    st.info(
        '⚠️ **Important:** This chat tab does NOT search databases. '
        'For finding real research papers and citations, use the **🔬 Prior Work Mapper** tab. '
        'The chat AI will never generate paper citations to avoid hallucination.',
        icon='🔬'
    )

    # Session and conversation
    session_id = get_or_create_session_id()

    if 'messages' not in st.session_state:
        st.session_state.messages = load_conversation(session_id)

    # Display conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Handle new user input
    if prompt := st.chat_input('Discuss a concept, mechanism, or research idea...'):

        save_message(session_id, 'user', prompt)
        st.session_state.messages.append({'role': 'user', 'content': prompt})

        with st.chat_message('user'):
            st.markdown(prompt)

        with st.chat_message('assistant'):

            # ── ROUTE: literature question → redirect, do not hallucinate ──
            if is_literature_question(prompt):
                response = (
                    "⚠️ **Literature search detected.**\n\n"
                    "I cannot safely retrieve or cite research papers from memory. "
                    "All language models — including me — can generate citations that "
                    "sound real but do not exist. This is called hallucination, and it "
                    "is especially dangerous in research contexts.\n\n"
                    "**Please use the 🔬 Prior Work Mapper tab** to search PubMed and "
                    "ArXiv for real, verified papers. Every result there links to an "
                    "actual paper you can open and read.\n\n"
                    "I am happy to help you with:\n"
                    "- Discussing the mechanism or biology behind your topic\n"
                    "- Interpreting results you have already found\n"
                    "- Challenging assumptions in your experimental design\n"
                    "- Explaining concepts at a mechanistic level\n\n"
                    "What would you like to discuss?"
                )
                st.markdown(response)

            # ── ROUTE: concept/discussion question → answer with AI ──
            else:
                with st.spinner('Thinking...'):

                    # Get relevant memories from past sessions
                    memory_context = build_memory_context(prompt)

                    # Build the system prompt
                    system = f'''You are an expert AI research thinking partner for a {level} in {domain if domain else 'life science'}.
{"Current project: " + project if project else ""}

CRITICAL RULES — NEVER VIOLATE THESE:

1. NEVER generate, fabricate, or cite research papers.
   Do not write author names, journal names, years, or paper titles.
   If you want to reference a concept, say "research in this area suggests..." without fabricating a citation.

2. NEVER say "According to Smith et al." or any author-year citation.
   You have not searched any database. You cannot safely cite papers.
   Direct the researcher to the Prior Work Mapper tab for any literature needs.

3. You CAN discuss mechanisms, concepts, pathways, experimental approaches, and established science.
   You CANNOT produce references, citations, or paper lists under any circumstances.

4. Flag uncertainty explicitly every time with phrases like:
   "I am not certain about this..."
   "This is my understanding but verify with the literature..."
   "The Prior Work Mapper will give you verified sources on this..."

DEPTH CALIBRATION:
This is a {level}. Do not give introductory or Wikipedia-level answers.
Give mechanistic depth, discuss conflicting models where they exist,
flag methodological debates, and engage at the level of someone reading primary literature.

PUSHBACK:
If the researcher's reasoning has a gap or assumption, challenge it directly.
End every substantive response with one pointed question that pushes their thinking further.

{"MEMORY FROM PREVIOUS SESSIONS:" + chr(10) + memory_context if memory_context else ""}'''

                    response = ask(st.session_state.messages, system_prompt=system)

                st.markdown(response)

        # Save the exchange
        save_message(session_id, 'assistant', response)
        st.session_state.messages.append({'role': 'assistant', 'content': response})

        # Add to semantic memory (non-critical — will not crash if it fails)
        try:
            add_memory(
                f'User asked: {prompt[:200]}. Response summary: {response[:300]}',
                category='CONVERSATION'
            )
        except Exception as e:
            print(f'Memory save failed (non-critical): {e}')


# ═════════════════════════════════════════════════════════════
# TAB 2: PRIOR WORK MAPPER
# ═════════════════════════════════════════════════════════════
with tab_research:
    st.header('🔬 Prior Work Mapper')
    st.caption(
        'Searches PubMed and ArXiv · Reads each paper individually · '
        'Returns a cited synthesis — every paper links to a real source you can open'
    )

    # Explainer
    with st.expander('How does this work?', expanded=False):
        st.markdown('''
**3-step process:**

1. **Search** — Your question is decomposed into focused sub-queries that search PubMed and ArXiv simultaneously
2. **Extract** — Each retrieved paper is read individually. We extract: main claim, methodology, evidence quality, key findings, and limitations
3. **Synthesise** — We reason across the extracted claims (not raw text) to produce a cited synthesis with gaps and contradictions identified

**Why this approach?**
Standard AI tools dump all papers into one prompt and summarise them — causing relevant findings in the middle to be skipped. We read each paper individually before synthesising, so every paper gets equal attention.
        ''')

    # Input
    research_question = st.text_area(
        'Enter your research question or topic:',
        placeholder=(
            'e.g. What is the current state of base editing for correcting point mutations in haematopoietic stem cells?\n'
            'e.g. What mechanisms regulate mTORC1 activity in nutrient-deprived conditions?\n'
            'e.g. Map the prior work on liquid-liquid phase separation in RNA granule formation.'
        ),
        height=120
    )

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        search_btn = st.button('🔍 Map Prior Work', type='primary', use_container_width=True)
    with col2:
        st.caption('Takes 1–3 minutes')

    # Run the search
    if search_btn and research_question.strip():

        with st.spinner('Step 1/3 — Decomposing query and searching PubMed + ArXiv...'):
            results = map_prior_work(
                research_question,
                ask,
                domain=domain or 'life science'
            )

        # ── RESULTS ──────────────────────────────────────────
        if results['status'] == 'complete':

            # Summary metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric('Papers Found', results.get('papers_found', 0))
            with col_b:
                confidence = results.get('confidence', 'Unknown')
                confidence_display = {
                    'STRONG': '🟢 Strong',
                    'MODERATE': '🟡 Moderate',
                    'PRELIMINARY': '🟠 Preliminary',
                    'THEORETICAL': '🔵 Theoretical'
                }.get(confidence, f'⚪ {confidence}')
                st.metric('Evidence Level', confidence_display)
            with col_b:
                sub_queries = results.get('sub_queries_used', [])
                st.metric('Sub-queries Run', len(sub_queries))

            # Sub-queries used (collapsed)
            if sub_queries:
                with st.expander('Sub-queries used in search', expanded=False):
                    for i, q in enumerate(sub_queries, 1):
                        st.markdown(f'{i}. {q}')

            st.divider()

            # Main synthesis
            st.subheader('📋 Research Synthesis')
            st.markdown(results.get('synthesis', 'No synthesis generated.'))

            st.divider()

            # Contradictions
            contradictions = results.get('contradictions', '')
            if contradictions and contradictions.strip() not in ['None identified.', 'None identified', '']:
                st.subheader('⚡ Contradictions in the Literature')
                st.warning(contradictions)
                st.divider()

            # Gaps
            gaps = results.get('gaps', '')
            if gaps:
                st.subheader('🔍 Identified Gaps')
                st.info(gaps)
                st.divider()

            # Follow-up question
            follow_up = results.get('follow_up_question', '')
            if follow_up:
                st.subheader('💭 A Question to Push Your Thinking')
                st.markdown(f'> *{follow_up}*')
                st.divider()

            # Citations
            citations = results.get('citations', [])
            if citations:
                st.subheader(f'📚 References ({len(citations)} papers)')
                st.caption('All papers below are real retrieved results — click links to verify')

                for cite in citations:
                    quality = cite.get('evidence_quality', 'Unknown')
                    quality_icon = {
                        'STRONG': '🟢',
                        'MODERATE': '🟡',
                        'PRELIMINARY': '🟠',
                        'THEORETICAL': '🔵',
                        'UNKNOWN': '⚪'
                    }.get(quality, '⚪')

                    source_badge = {
                        'PubMed': '🔵 PubMed',
                        'ArXiv': '🟣 ArXiv',
                        'Semantic Scholar': '🟡 Semantic Scholar'
                    }.get(cite.get('source', ''), cite.get('source', ''))

                    citation_line = (
                        f"**{cite.get('number', '')}. {cite.get('authors', 'Unknown')}** "
                        f"({cite.get('year', 'Unknown')}). "
                        f"{cite.get('title', 'Unknown title')}. "
                        f"*{source_badge}* {quality_icon}"
                    )

                    if cite.get('url'):
                        st.markdown(f"{citation_line} — [Open paper ↗]({cite['url']})")
                    else:
                        st.markdown(citation_line)

            # Save to semantic memory
            try:
                memory_text = (
                    f'Prior work search on: {research_question[:150]}. '
                    f'Found {results.get("papers_found", 0)} papers. '
                    f'Synthesis: {results.get("synthesis", "")[:300]}'
                )
                add_memory(memory_text, category='RESEARCH_FINDING')
            except Exception as e:
                print(f'Research memory save failed (non-critical): {e}')

        elif results['status'] == 'no_results':
            st.warning(
                results.get('synthesis', 'No papers found.')
                + '\n\nTry rephrasing with more specific scientific terminology, '
                'or break your question into a more focused sub-topic.'
            )

        else:
            st.error(
                f"Search encountered an error: {results.get('error', 'Unknown error')}\n\n"
                "Please try again or rephrase your question."
            )

    elif search_btn and not research_question.strip():
        st.warning('Please enter a research question before searching.')