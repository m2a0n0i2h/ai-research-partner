# test_pubmed.py
from src.research.pubmed import search_pubmed

# Test with a real life science query
papers = search_pubmed('CRISPR base editing mechanism 2023', max_results=5)

print(f'Found {len(papers)} papers')
print()

for i, paper in enumerate(papers, 1):
    print(f'Paper {i}:')
    print(f'  Title: {paper["title"]}')
    print(f'  Authors: {paper["authors"]}')
    print(f'  Year: {paper["year"]}')
    print(f'  Journal: {paper["journal"]}')
    print(f'  URL: {paper["url"]}')
    print(f'  Abstract (first 200 chars): {paper["abstract"][:200]}...')
    print()
