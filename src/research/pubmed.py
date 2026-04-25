# src/research/pubmed.py
from Bio import Entrez
import xml.etree.ElementTree as ET
import time

# NCBI requires an email address for identification
# Replace with your actual email
Entrez.email = 'm.kaushik9502@gmail.com'

# Optional: add your free NCBI API key here for higher rate limits
Entrez.api_key = 'f1a4e2f940af69bd73cf02317d9c9201ee08'

def search_pubmed(query: str, max_results: int = 10) -> list:
    '''
    Search PubMed for papers matching a query.
    Returns a list of paper dictionaries.
    '''
    try:
        # Step 1: Search PubMed for matching paper IDs
        search_handle = Entrez.esearch(
            db='pubmed',
            term=query,
            retmax=max_results,
            sort='relevance'
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()

        paper_ids = search_results['IdList']

        if not paper_ids:
            return []

        # Small delay to respect NCBI rate limits
        time.sleep(0.34)

        # Step 2: Fetch full details for those paper IDs
        fetch_handle = Entrez.efetch(
            db='pubmed',
            id=paper_ids,
            rettype='xml',
            retmode='xml'
        )
        raw_xml = fetch_handle.read()
        fetch_handle.close()

        # Step 3: Parse the XML response
        return _parse_pubmed_xml(raw_xml)

    except Exception as e:
        print(f'PubMed search error: {e}')
        return []

def _parse_pubmed_xml(xml_data: bytes) -> list:
    '''Parse PubMed XML and extract structured paper data.'''
    papers = []

    try:
        root = ET.fromstring(xml_data)

        for article in root.findall('.//PubmedArticle'):
            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else 'No title'
            # Remove any HTML tags from title
            if title:
                title = title.strip()

            # Extract abstract
            abstract_parts = article.findall('.//AbstractText')
            if abstract_parts:
                abstract = ' '.join([
                    (p.text or '') for p in abstract_parts if p.text
                ])
            else:
                abstract = 'No abstract available'

            # Extract authors
            authors = []
            for author in article.findall('.//Author'):
                last = author.findtext('LastName', default='')
                first = author.findtext('ForeName', default='')
                if last:
                    authors.append(f'{last} {first}'.strip())
            author_string = ', '.join(authors[:3])
            if len(authors) > 3:
                author_string += ' et al.'

            # Extract year
            year = article.findtext('.//PubDate/Year', default='')
            if not year:
                year = article.findtext('.//PubDate/MedlineDate', default='Unknown')[:4]

            # Extract PubMed ID
            pmid = article.findtext('.//PMID', default='')

            # Extract journal name
            journal = article.findtext('.//Journal/Title', default='')

            papers.append({
                'source': 'PubMed',
                'title': title,
                'abstract': abstract,
                'authors': author_string,
                'year': year,
                'journal': journal,
                'pmid': pmid,
                'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/' if pmid else ''
            })

    except Exception as e:
        print(f'PubMed XML parsing error: {e}')

    return papers
