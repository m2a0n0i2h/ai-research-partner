# src/research/extractor.py
import time


def extract_claims_from_paper(paper: dict, ask_fn) -> dict:
    '''
    Read a single paper and extract structured information.
    Every paper gets individual attention — this is the staged reading fix.
    '''
    paper_text = f'''
Title: {paper.get('title', 'Unknown')}
Authors: {paper.get('authors', 'Unknown')}
Year: {paper.get('year', 'Unknown')}
Journal: {paper.get('journal', 'Unknown')}
Source: {paper.get('source', 'Unknown')}
Abstract: {paper.get('abstract', 'No abstract available')}
'''

    extraction_prompt = f'''You are a scientific paper analyser. Extract structured information from this paper.
Be precise and concise. If information is not available, write "Not stated".

{paper_text}

Extract and return EXACTLY this structure with no extra text:
MAIN_CLAIM: [The single most important finding or claim in one sentence]
METHODOLOGY: [The experimental approach — e.g. RCT, in vitro, computational, meta-analysis]
SAMPLE_SIZE: [Number of subjects/samples, or "Not applicable" for computational work]
KEY_FINDINGS: [2-3 specific findings with numbers where available]
LIMITATIONS: [Main limitations stated or implied]
EVIDENCE_QUALITY: [STRONG / MODERATE / PRELIMINARY / THEORETICAL]
RELEVANCE_NOTE: [One sentence on why this paper matters]
'''

    try:
        response = ask_fn(
            [{'role': 'user', 'content': extraction_prompt}],
            system_prompt='You are a precise scientific paper analyser. Extract exactly what is asked. Be concise. Never skip any field.'
        )

        extraction = _parse_extraction(response)

        # Always attach paper metadata
        extraction['title'] = paper.get('title', 'Unknown')
        extraction['authors'] = paper.get('authors', 'Unknown')
        extraction['year'] = paper.get('year', 'Unknown')
        extraction['source'] = paper.get('source', 'Unknown')
        extraction['url'] = paper.get('url', '')
        extraction['citation_count'] = paper.get('citation_count', 0)

        # Make sure evidence_quality always has a value
        if not extraction.get('evidence_quality'):
            extraction['evidence_quality'] = 'MODERATE'

        # Make sure main_claim always has a value
        if not extraction.get('main_claim'):
            abstract = paper.get('abstract', '')
            extraction['main_claim'] = abstract[:200] if abstract else 'Not extracted'

        return extraction

    except Exception as e:
        print(f'Extraction error for "{paper.get("title", "Unknown")}": {e}')
        return _fallback_extraction(paper, str(e))


def extract_all_papers(papers: list, ask_fn, max_papers: int = 15) -> list:
    '''
    Extract claims from multiple papers one at a time.
    Processes up to max_papers papers individually.
    Uses a short delay between calls to avoid rate limits.
    '''
    extractions = []
    papers_to_process = papers[:max_papers]

    print(f'Extracting claims from {len(papers_to_process)} papers individually...')

    for i, paper in enumerate(papers_to_process, 1):
        title_preview = paper.get('title', 'Unknown')[:60]
        print(f'  Paper {i}/{len(papers_to_process)}: {title_preview}...')

        extraction = extract_claims_from_paper(paper, ask_fn)
        extractions.append(extraction)

        # Delay between API calls to respect Groq rate limits
        # Shorter delay for first 8, slightly longer after to avoid 429
        if i < 8:
            time.sleep(0.8)
        else:
            time.sleep(1.2)

    print(f'Extraction complete. {len(extractions)} papers processed.')
    return extractions


def _parse_extraction(response: str) -> dict:
    '''Parse the structured extraction from the AI response.'''
    result = {}

    field_map = {
        'MAIN_CLAIM': 'main_claim',
        'METHODOLOGY': 'methodology',
        'SAMPLE_SIZE': 'sample_size',
        'KEY_FINDINGS': 'key_findings',
        'LIMITATIONS': 'limitations',
        'EVIDENCE_QUALITY': 'evidence_quality',
        'RELEVANCE_NOTE': 'relevance_note',
    }

    lines = response.split('\n')
    current_field = None
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        matched = False
        for field_label, field_key in field_map.items():
            if line.upper().startswith(f'{field_label}:'):
                # Save previous field
                if current_field:
                    result[current_field] = ' '.join(current_content).strip()
                current_field = field_key
                content = line[len(field_label)+1:].strip()
                current_content = [content] if content else []
                matched = True
                break

        if not matched and current_field and line:
            current_content.append(line)

    # Save the last field
    if current_field:
        result[current_field] = ' '.join(current_content).strip()

    return result


def _fallback_extraction(paper: dict, error: str = '') -> dict:
    '''
    Return a basic extraction when the API call fails.
    Uses the abstract as the main claim so the paper is still useful.
    '''
    abstract = paper.get('abstract', '')
    return {
        'title': paper.get('title', 'Unknown'),
        'authors': paper.get('authors', 'Unknown'),
        'year': paper.get('year', 'Unknown'),
        'source': paper.get('source', 'Unknown'),
        'url': paper.get('url', ''),
        'citation_count': paper.get('citation_count', 0),
        'main_claim': abstract[:300] if abstract else 'Abstract not available',
        'methodology': 'See abstract',
        'sample_size': 'Not extracted',
        'key_findings': abstract[:200] if abstract else 'Not extracted',
        'limitations': 'Not extracted',
        'evidence_quality': 'MODERATE',
        'relevance_note': 'Included based on search relevance',
        'error': error
    }