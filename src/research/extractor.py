# src/research/extractor.py

def extract_claims_from_paper(paper: dict, ask_fn) -> dict:
    '''
    Read a single paper and extract structured information.
    Used for high-priority papers — full individual extraction.
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

Extract and return EXACTLY this structure:
MAIN_CLAIM: [The single most important finding or claim in one sentence]
METHODOLOGY: [The experimental approach — e.g. RCT, in vitro, computational, meta-analysis]
SAMPLE_SIZE: [Number of subjects/samples, or "Not applicable" for computational work]
KEY_FINDINGS: [2-3 specific findings with numbers where available]
LIMITATIONS: [Main limitations stated or implied]
EVIDENCE_QUALITY: [Rate as: STRONG / MODERATE / PRELIMINARY / THEORETICAL]
RELEVANCE_NOTE: [One sentence on why this paper matters]
'''

    try:
        response = ask_fn(
            [{'role': 'user', 'content': extraction_prompt}],
            system_prompt='You are a precise scientific paper analyser. Extract exactly what is asked. Be concise.'
        )

        extraction = _parse_extraction(response)
        extraction['title'] = paper.get('title', 'Unknown')
        extraction['authors'] = paper.get('authors', 'Unknown')
        extraction['year'] = paper.get('year', 'Unknown')
        extraction['source'] = paper.get('source', 'Unknown')
        extraction['url'] = paper.get('url', '')
        extraction['citation_count'] = paper.get('citation_count', 0)
        return extraction

    except Exception as e:
        print(f'Extraction error for "{paper.get("title", "Unknown")}": {e}')
        return _fallback_extraction(paper, str(e))


def extract_batch(papers: list, ask_fn) -> list:
    '''
    Extract claims from a batch of papers in one API call.
    Used for lower-priority papers to save API calls.
    Each batch is maximum 3 papers.
    '''
    if not papers:
        return []

    batch_text = ''
    for i, paper in enumerate(papers, 1):
        batch_text += f'''
PAPER {i}:
Title: {paper.get('title', 'Unknown')}
Authors: {paper.get('authors', 'Unknown')}
Year: {paper.get('year', 'Unknown')}
Abstract: {paper.get('abstract', 'No abstract')[:400]}
---
'''

    batch_prompt = f'''You are a scientific paper analyser. Extract structured information from each paper below.

{batch_text}

For EACH paper return EXACTLY this format:

PAPER 1:
MAIN_CLAIM: [one sentence]
METHODOLOGY: [approach used]
EVIDENCE_QUALITY: [STRONG / MODERATE / PRELIMINARY / THEORETICAL]
KEY_FINDINGS: [1-2 key findings]
LIMITATIONS: [main limitation]

PAPER 2:
MAIN_CLAIM: [one sentence]
METHODOLOGY: [approach used]
EVIDENCE_QUALITY: [STRONG / MODERATE / PRELIMINARY / THEORETICAL]
KEY_FINDINGS: [1-2 key findings]
LIMITATIONS: [main limitation]

And so on for all {len(papers)} papers.
'''

    try:
        response = ask_fn(
            [{'role': 'user', 'content': batch_prompt}],
            system_prompt='You are a precise scientific paper analyser. Extract exactly what is asked for each paper.'
        )

        # Parse batch response into individual extractions
        extractions = _parse_batch_response(response, papers)
        return extractions

    except Exception as e:
        print(f'Batch extraction error: {e}')
        # Fall back to basic extraction for each paper
        return [_fallback_extraction(p, str(e)) for p in papers]


def _parse_batch_response(response: str, papers: list) -> list:
    '''Parse a batch extraction response into individual paper extractions.'''
    extractions = []

    # Split response by PAPER N: markers
    import re
    sections = re.split(r'PAPER\s+\d+:', response, flags=re.IGNORECASE)

    # Remove empty first section
    sections = [s.strip() for s in sections if s.strip()]

    for i, (paper, section) in enumerate(zip(papers, sections)):
        # Parse this section using the standard parser
        field_map = {
            'MAIN_CLAIM': 'main_claim',
            'METHODOLOGY': 'methodology',
            'EVIDENCE_QUALITY': 'evidence_quality',
            'KEY_FINDINGS': 'key_findings',
            'LIMITATIONS': 'limitations',
        }

        result = {}
        lines = section.split('\n')
        current_field = None
        current_content = []

        for line in lines:
            line = line.strip()
            matched = False
            for label, key in field_map.items():
                if line.startswith(f'{label}:'):
                    if current_field:
                        result[current_field] = ' '.join(current_content).strip()
                    current_field = key
                    content = line[len(label)+1:].strip()
                    current_content = [content] if content else []
                    matched = True
                    break
            if not matched and current_field and line:
                current_content.append(line)

        if current_field:
            result[current_field] = ' '.join(current_content).strip()

        # Add paper metadata
        result['title'] = paper.get('title', 'Unknown')
        result['authors'] = paper.get('authors', 'Unknown')
        result['year'] = paper.get('year', 'Unknown')
        result['source'] = paper.get('source', 'Unknown')
        result['url'] = paper.get('url', '')
        result['citation_count'] = paper.get('citation_count', 0)
        result.setdefault('main_claim', 'Not extracted')
        result.setdefault('evidence_quality', 'UNKNOWN')

        extractions.append(result)

    # If parsing failed, return fallback extractions
    if len(extractions) < len(papers):
        for paper in papers[len(extractions):]:
            extractions.append(_fallback_extraction(paper, 'Batch parse failed'))

    return extractions


def extract_all_papers(papers: list, ask_fn, max_papers: int = 20) -> list:
    '''
    Extract claims from multiple papers using a smart two-tier approach:
    - Top 8 papers: full individual extraction (one API call each)
    - Remaining papers: batch extraction (3 papers per API call)

    This allows citing up to 20 papers while staying within rate limits.
    '''
    import time

    papers_to_process = papers[:max_papers]
    print(f'Processing {len(papers_to_process)} papers total...')

    extractions = []

    # Tier 1: Full individual extraction for top 8 papers
    top_papers = papers_to_process[:8]
    print(f'Tier 1: Full extraction for top {len(top_papers)} papers...')

    for i, paper in enumerate(top_papers, 1):
        print(f'  Reading paper {i}/{len(top_papers)}: {paper.get("title", "")[:60]}...')
        extraction = extract_claims_from_paper(paper, ask_fn)
        extractions.append(extraction)
        # Small delay to respect rate limits
        time.sleep(0.5)

    # Tier 2: Batch extraction for remaining papers (groups of 3)
    remaining_papers = papers_to_process[8:]
    if remaining_papers:
        print(f'Tier 2: Batch extraction for {len(remaining_papers)} additional papers...')

        # Process in batches of 3
        batch_size = 3
        for i in range(0, len(remaining_papers), batch_size):
            batch = remaining_papers[i:i + batch_size]
            print(f'  Batch {i//batch_size + 1}: processing {len(batch)} papers...')
            batch_extractions = extract_batch(batch, ask_fn)
            extractions.extend(batch_extractions)
            time.sleep(1)  # Slightly longer delay between batches

    print(f'Extraction complete. {len(extractions)} papers processed.')
    return extractions


def _parse_extraction(response: str) -> dict:
    '''Parse a single paper extraction response.'''
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
        matched = False
        for field_label, field_key in field_map.items():
            if line.startswith(f'{field_label}:'):
                if current_field:
                    result[current_field] = ' '.join(current_content).strip()
                current_field = field_key
                content = line[len(field_label)+1:].strip()
                current_content = [content] if content else []
                matched = True
                break
        if not matched and current_field and line:
            current_content.append(line)

    if current_field:
        result[current_field] = ' '.join(current_content).strip()

    return result


def _fallback_extraction(paper: dict, error: str = '') -> dict:
    '''Return a basic extraction when the API call fails.'''
    return {
        'title': paper.get('title', 'Unknown'),
        'authors': paper.get('authors', 'Unknown'),
        'year': paper.get('year', 'Unknown'),
        'source': paper.get('source', 'Unknown'),
        'url': paper.get('url', ''),
        'citation_count': paper.get('citation_count', 0),
        'main_claim': paper.get('abstract', 'No abstract')[:200] if paper.get('abstract') else 'Not extracted',
        'methodology': 'Not extracted',
        'evidence_quality': 'UNKNOWN',
        'key_findings': 'Not extracted',
        'limitations': 'Not extracted',
        'error': error
    }