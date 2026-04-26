# src/research/synthesiser.py

def synthesise_research(query: str, extractions: list, ask_fn) -> dict:
    '''
    Synthesise research findings from structured paper extractions.
    Returns synthesis, citations, gaps, contradictions, and confidence.
    '''
    if not extractions:
        return {
            'synthesis': 'No papers found for this query.',
            'citations': [],
            'gaps': 'Unable to identify gaps without papers.',
            'contradictions': 'None identified.',
            'confidence': 'LOW',
            'follow_up_question': ''
        }

    extraction_block = _build_extraction_block(extractions)

    synthesis_prompt = f'''You are a senior life science researcher synthesising literature.
You have structured extractions from {len(extractions)} papers about: {query}

PAPER EXTRACTIONS:
{extraction_block}

Write a PhD-level research synthesis that:
1. States the overall state of knowledge on this topic
2. Highlights key findings with author-year citations in brackets e.g. (Smith et al., 2023)
3. Identifies where papers AGREE and where they CONTRADICT each other
4. Flags which findings are well-established vs preliminary
5. Identifies 2-3 clear gaps in the current literature
6. Ends with a pointed question that challenges the researcher

Format your response EXACTLY as:
SYNTHESIS:
[Your 3-4 paragraph synthesis with inline citations]

CONTRADICTIONS:
[Any conflicting findings, or "None identified"]

GAPS:
[2-3 specific gaps in the literature]

CONFIDENCE:
[STRONG / MODERATE / PRELIMINARY]

FOLLOW_UP_QUESTION:
[One challenging question for the researcher]
'''

    try:
        response = ask_fn(
            [{'role': 'user', 'content': synthesis_prompt}],
            system_prompt='''You are a senior life science researcher.
Give mechanistic depth. Use exact citations from the extractions provided.
Never assert something you cannot attribute to a specific extraction.
Flag uncertainty explicitly.'''
        )

        parsed = _parse_synthesis(response)
        parsed['citations'] = _build_citation_list(extractions)
        parsed['paper_count'] = len(extractions)
        return parsed

    except Exception as e:
        return {
            'synthesis': f'Synthesis failed: {str(e)}',
            'citations': _build_citation_list(extractions),
            'gaps': 'Unknown',
            'contradictions': 'Unknown',
            'confidence': 'LOW',
            'follow_up_question': ''
        }


def _build_extraction_block(extractions: list) -> str:
    '''Format extractions for the synthesis prompt.'''
    block = ''
    for i, ext in enumerate(extractions, 1):
        block += f'''
Paper {i}: {ext.get('authors', 'Unknown')} ({ext.get('year', 'Unknown')})
Title: {ext.get('title', 'Unknown')}
Main claim: {ext.get('main_claim', 'Not extracted')}
Methodology: {ext.get('methodology', 'Unknown')}
Key findings: {ext.get('key_findings', 'Not extracted')}
Evidence quality: {ext.get('evidence_quality', 'Unknown')}
Limitations: {ext.get('limitations', 'Not stated')}
---'''
    return block


def _parse_synthesis(response: str) -> dict:
    '''Parse the structured synthesis response.'''
    result = {
        'synthesis': '',
        'contradictions': 'None identified.',
        'gaps': '',
        'confidence': 'MODERATE',
        'follow_up_question': ''
    }

    sections = {
        'SYNTHESIS:': 'synthesis',
        'CONTRADICTIONS:': 'contradictions',
        'GAPS:': 'gaps',
        'CONFIDENCE:': 'confidence',
        'FOLLOW_UP_QUESTION:': 'follow_up_question'
    }

    current_section = None
    current_content = []

    for line in response.split('\n'):
        matched = False
        for header, key in sections.items():
            if line.strip().startswith(header):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = key
                remainder = line.strip()[len(header):].strip()
                current_content = [remainder] if remainder else []
                matched = True
                break
        if not matched and current_section:
            current_content.append(line)

    if current_section:
        result[current_section] = '\n'.join(current_content).strip()

    return result


def _build_citation_list(extractions: list) -> list:
    '''Build a numbered citation list from extractions.'''
    citations = []
    for i, ext in enumerate(extractions, 1):
        citations.append({
            'number': i,
            'authors': ext.get('authors', 'Unknown'),
            'year': ext.get('year', 'Unknown'),
            'title': ext.get('title', 'Unknown'),
            'source': ext.get('source', 'Unknown'),
            'url': ext.get('url', ''),
            'evidence_quality': ext.get('evidence_quality', 'Unknown'),
        })
    return citations