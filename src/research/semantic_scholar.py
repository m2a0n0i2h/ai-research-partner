
import os
headers={
    'User-Agent': 'AIResearchPartner/1.0',
    'x-api-key': os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')
}
# src/research/semantic_scholar.py
import requests
import time

BASE_URL = 'https://api.semanticscholar.org/graph/v1'
FIELDS = 'title,abstract,authors,year,journal,citationCount,influentialCitationCount,externalIds,openAccessPdf'

def search_semantic_scholar(query: str, max_results: int = 10) -> list:
    '''
    Search Semantic Scholar with automatic retry on rate limit.
    '''
    max_retries = 3
    retry_delay = 5  # seconds to wait before retrying

    for attempt in range(max_retries):
        try:
            response = requests.get(
                f'{BASE_URL}/paper/search',
                params={
                    'query': query,
                    'limit': max_results,
                    'fields': FIELDS
                },
                headers={'User-Agent': 'AIResearchPartner/1.0'},
                timeout=15
            )

            # Rate limit hit — wait and retry
            if response.status_code == 429:
                wait_time = retry_delay * (attempt + 1)
                print(f'Semantic Scholar rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...')
                time.sleep(wait_time)
                continue

            if response.status_code != 200:
                print(f'Semantic Scholar error: {response.status_code}')
                return []

            data = response.json()
            papers = []

            for item in data.get('data', []):
                authors = [a.get('name', '') for a in item.get('authors', [])[:3]]
                author_string = ', '.join(authors)
                if len(item.get('authors', [])) > 3:
                    author_string += ' et al.'

                paper_id = item.get('paperId', '')
                url = f'https://www.semanticscholar.org/paper/{paper_id}' if paper_id else ''

                pdf_info = item.get('openAccessPdf') or {}
                pdf_url = pdf_info.get('url', '')

                journal_info = item.get('journal') or {}
                journal = journal_info.get('name', 'Unknown Journal')

                papers.append({
                    'source': 'Semantic Scholar',
                    'title': item.get('title', 'No title'),
                    'abstract': item.get('abstract', 'No abstract available') or 'No abstract available',
                    'authors': author_string,
                    'year': str(item.get('year', 'Unknown')),
                    'journal': journal,
                    'citation_count': item.get('citationCount', 0),
                    'influential_citations': item.get('influentialCitationCount', 0),
                    'url': url,
                    'pdf_url': pdf_url,
                })

                time.sleep(0.1)

            return papers

        except Exception as e:
            print(f'Semantic Scholar error (attempt {attempt + 1}): {e}')
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    # All retries failed — return empty list so other databases still work
    print('Semantic Scholar unavailable after retries. Continuing with PubMed and ArXiv only.')
    return []