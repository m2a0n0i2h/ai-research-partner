# src/research/extractor.py

def extract_claims_from_paper(paper: dict, ask_fn) -> dict:
    '''
    Read a single paper and extract structured information.
    This is the staged reading fix — every paper gets individual attention.
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
RELEVANCE_NOTE: [One sentence on why this paper matters for the research question]
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
        return {
            'title': paper.get('title', 'Unknown'),
            'authors': paper.get('authors', 'Unknown'),
            'year': paper.get('year', 'Unknown'),
            'source': paper.get('source', 'Unknown'),
            'url': paper.get('url', ''),
            'main_claim': 'Extraction failed',
            'methodology': 'Unknown',
            'evidence_quality': 'UNKNOWN',
            'error': str(e)
        }


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


def extract_all_papers(papers: list, ask_fn, max_papers: int = 8) -> list:
    '''
    Extract claims from multiple papers one at a time.
    This is staged reading — every paper gets individual attention.
    max_papers limits processing to avoid rate limits.
    '''
    extractions = []
    papers_to_process = papers[:max_papers]

    print(f'Extracting claims from {len(papers_to_process)} papers individually...')

    for i, paper in enumerate(papers_to_process, 1):
        print(f'  Reading paper {i}/{len(papers_to_process)}: {paper.get("title", "")[:60]}...')
        extraction = extract_claims_from_paper(paper, ask_fn)
        extractions.append(extraction)

    print(f'Extraction complete. {len(extractions)} papers processed.')
    return extractions