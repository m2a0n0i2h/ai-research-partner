# test_unified.py
from src.research.unified_search import unified_search

papers = unified_search('CRISPR gene editing cancer therapy', max_per_source=5)

print(f'Total unique papers found: {len(papers)}')
print()
for i, p in enumerate(papers, 1):
    print(f'{i}. [{p["source"]}] [{p["year"]}] {p["title"][:80]}')
