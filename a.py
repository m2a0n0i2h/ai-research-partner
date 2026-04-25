# test_databases.py
from src.research.arxiv_search import search_arxiv
from src.research.semantic_scholar import search_semantic_scholar

query = 'transformer models biomedical text mining'

print('=== ARXIV RESULTS ===')
arxiv_papers = search_arxiv(query, max_results=3)
for p in arxiv_papers:
    print(f'  [{p["year"]}] {p["title"]}')
    print(f'  URL: {p["url"]}')
    print()

print('=== SEMANTIC SCHOLAR RESULTS ===')
ss_papers = search_semantic_scholar(query, max_results=3)
for p in ss_papers:
    print(f'  [{p["year"]}] {p["title"]}')
    print(f'  Citations: {p["citation_count"]}')
    print(f'  URL: {p["url"]}')
    print()
