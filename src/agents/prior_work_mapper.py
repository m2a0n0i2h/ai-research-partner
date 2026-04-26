# src/agents/prior_work_mapper.py
from src.research.unified_search import unified_search, decompose_query, _deduplicate_papers
from src.research.extractor import extract_all_papers
from src.research.synthesiser import synthesise_research

def map_prior_work(research_question: str, ask_fn, domain: str = 'life science') -> dict:
    '''
    Full pipeline: question → search → extract → synthesise → structured output.
    '''
    result = {
        'query': research_question,
        'status': 'running',
        'papers_found': 0,
        'synthesis': '',
        'citations': [],
        'gaps': '',
        'contradictions': '',
        'confidence': '',
        'follow_up_question': '',
        'sub_queries_used': [],
        'error': None
    }

    try:
        # Stage 1: Decompose the question into targeted sub-queries
        print('Stage 1: Decomposing query...')
        sub_queries = decompose_query(research_question, ask_fn)
        print(f'  Sub-queries: {sub_queries}')
        result['sub_queries_used'] = sub_queries

        # Stage 2: Search all databases for each sub-query
        print('Stage 2: Searching databases...')
        all_papers = []
        for sub_query in sub_queries:
            papers = unified_search(sub_query, max_per_source=5)
            all_papers.extend(papers)

        # Deduplicate across sub-query results
        all_papers = _deduplicate_papers(all_papers)
        result['papers_found'] = len(all_papers)
        print(f'  Total unique papers: {len(all_papers)}')

        if not all_papers:
            result['status'] = 'no_results'
            result['synthesis'] = (
                'No papers found for this research question. '
                'This may mean the topic is very new, uses different terminology, '
                'or has not been published in indexed databases yet. '
                'Try rephrasing with more specific scientific terminology.'
            )
            return result

        # Stage 3: Extract claims from each paper individually
        print('Stage 3: Staged reading...')
        extractions = extract_all_papers(all_papers, ask_fn, max_papers=20)

        # Stage 4: Synthesise across extractions
        print('Stage 4: Synthesising...')
        synthesis_result = synthesise_research(research_question, extractions, ask_fn)

        result.update(synthesis_result)
        result['status'] = 'complete'
        return result

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        print(f'Prior Work Mapper error: {e}')
        return result