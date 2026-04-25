# src/research/unified_search.py
from src.research.pubmed import search_pubmed
from src.research.arxiv_search import search_arxiv
from src.research.semantic_scholar import search_semantic_scholar
import re

def unified_search(query: str, max_per_source: int = 8) -> list:
    '''
    Search all three databases and return deduplicated results.
    Papers are ranked by relevance and recency.
    '''
    print(f'Searching databases for: {query}')

    # Search all three databases
    pubmed_papers = search_pubmed(query, max_results=max_per_source)
    print(f'  PubMed: {len(pubmed_papers)} papers')

    arxiv_papers = search_arxiv(query, max_results=max_per_source)
    print(f'  ArXiv: {len(arxiv_papers)} papers')

    ss_papers = search_semantic_scholar(query, max_results=max_per_source)
    print(f'  Semantic Scholar: {len(ss_papers)} papers')

    # Combine all papers
    all_papers = pubmed_papers + arxiv_papers + ss_papers

    # Deduplicate by title similarity
    deduplicated = _deduplicate_papers(all_papers)
    print(f'  After deduplication: {len(deduplicated)} unique papers')

    # Sort by year (most recent first)
    deduplicated.sort(key=lambda x: x.get('year', '0'), reverse=True)

    return deduplicated

def _normalise_title(title: str) -> str:
    '''Normalise title for comparison — lowercase, remove punctuation.'''
    if not title:
        return ''
    title = title.lower()
    title = re.sub(r'[^a-z0-9 ]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def _titles_are_similar(title1: str, title2: str, threshold: float = 0.85) -> bool:
    '''Check if two titles are similar enough to be considered duplicates.'''
    t1 = _normalise_title(title1)
    t2 = _normalise_title(title2)

    if not t1 or not t2:
        return False

    # Simple word overlap similarity
    words1 = set(t1.split())
    words2 = set(t2.split())

    if not words1 or not words2:
        return False

    intersection = words1 & words2
    union = words1 | words2
    similarity = len(intersection) / len(union)

    return similarity >= threshold

def _deduplicate_papers(papers: list) -> list:
    '''Remove duplicate papers based on title similarity.'''
    unique_papers = []

    for paper in papers:
        is_duplicate = False
        for existing in unique_papers:
            if _titles_are_similar(paper['title'], existing['title']):
                is_duplicate = True
                # Keep the one with more information (e.g. has citation count)
                if paper.get('citation_count', 0) > existing.get('citation_count', 0):
                    unique_papers.remove(existing)
                    unique_papers.append(paper)
                break
        if not is_duplicate:
            unique_papers.append(paper)

    return unique_papers

def decompose_query(query: str, groq_client_ask) -> list:
    '''
    Break a complex research question into focused sub-queries.
    Uses the AI to decompose — more targeted searches, better results.
    '''
    prompt = f'''Break this research question into 3 focused search queries for PubMed/ArXiv.
Each query should target a different aspect of the question.
Return ONLY a Python list of 3 strings, nothing else.
Example format: ["query one", "query two", "query three"]

Research question: {query}'''

    try:
        response = groq_client_ask(
            [{'role': 'user', 'content': prompt}],
            system_prompt='You are a scientific search query expert. Return only valid Python lists.'
        )

        # Extract the list from the response
        import ast
        # Find content between [ and ]
        start = response.find('[')
        end = response.rfind(']') + 1
        if start != -1 and end > start:
            queries = ast.literal_eval(response[start:end])
            return queries[:3]  # Maximum 3 sub-queries
    except Exception as e:
        print(f'Query decomposition failed: {e}')

    # Fallback: return original query as single item
    return [query]
