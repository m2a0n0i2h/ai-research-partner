# src/research/arxiv_search.py
import arxiv
import time

def search_arxiv(query: str, max_results: int = 10) -> list:
    '''
    Search ArXiv for papers matching a query.
    Great for AI/ML papers and biology preprints (q-bio category).
    '''
    try:
        # Create ArXiv client
        client = arxiv.Client()

        # Build search — include both CS and biology categories
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = []
        for result in client.results(search):
            # Extract authors (first 3 only)
            authors = [a.name for a in result.authors[:3]]
            author_string = ', '.join(authors)
            if len(result.authors) > 3:
                author_string += ' et al.'

            papers.append({
                'source': 'ArXiv',
                'title': result.title,
                'abstract': result.summary,
                'authors': author_string,
                'year': str(result.published.year),
                'journal': 'ArXiv Preprint',
                'arxiv_id': result.entry_id.split('/')[-1],
                'url': result.entry_id,
                'categories': [c for c in result.categories],
            })

            # Small delay between requests
            time.sleep(0.1)

        return papers

    except Exception as e:
        print(f'ArXiv search error: {e}')
        return []
