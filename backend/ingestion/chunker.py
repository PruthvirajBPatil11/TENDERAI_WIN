"""
Document chunker - splits documents into labeled sections.
"""

import logging
import re

logger = logging.getLogger(__name__)


def chunk_document(pages: list[dict]) -> list[dict]:
    """
    Split document into labeled sections based on government tender headers.
    
    Args:
        pages: List of page dicts from ingestion pipeline
        
    Returns:
        List of section dicts with keys: section_name, text, page_nos
    """
    # Common section headers in government tenders - updated to match section headers more precisely
    section_patterns = [
        # Match section headers (with surrounding lines/equals signs)
        (r"(?:^|\n)\s*(?:section\s*[-:]?\s*)?eligibility\s+criteria\s*(?:\n|=)", "Eligibility Criteria"),
        (r"(?:^|\n)\s*technical\s+(?:requirement|specification)s?\s*(?:\n|=)", "Technical Requirements"),
        (r"(?:^|\n)\s*financial\s+(?:requirement|qualification)s?\s*(?:\n|=)", "Financial Requirements"),
        (r"(?:^|\n)\s*scope\s+of\s+work\s*(?:\n|=)", "Scope of Work"),
        (r"(?:^|\n)\s*general\s+(?:condition|terms?)\s*(?:\n|=)", "General Conditions"),
        (r"(?:^|\n)\s*qualification\s+(?:requirement)?s?\s*(?:\n|=)", "Qualifications"),
        (r"(?:^|\n)\s*experience\s+requirement\s*(?:\n|=)", "Experience Requirements"),
    ]
    
    # Combine all text
    full_text = ""
    page_mapping = []  # Track which original page each character came from
    
    for page in pages:
        text = page.get("text", "")
        page_no = page.get("page_no", 0)
        
        start_pos = len(full_text)
        full_text += text + "\n\n"
        end_pos = len(full_text)
        
        page_mapping.append((start_pos, end_pos, page_no))
    
    # Find ALL section matches across the entire document
    all_matches = []
    for pattern, section_name in section_patterns:
        matches = list(re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE))
        for match in matches:
            # Get the position right after the header line (where content starts)
            match_end = match.end()
            # Skip past any newlines or equals signs
            while match_end < len(full_text) and full_text[match_end] in '\n=':
                match_end += 1
            all_matches.append((match_end, section_name))
            logger.debug(f"Found section header '{section_name}' at position {match.start()}")
    
    # Sort by position in document
    all_matches.sort(key=lambda x: x[0])
    
    # Remove duplicates - keep only first occurrence of each position-based section
    unique_matches = []
    seen_positions = set()
    for pos, name in all_matches:
        if pos not in seen_positions:
            unique_matches.append((pos, name))
            seen_positions.add(pos)
    
    all_matches = unique_matches
    
    # Build sections by finding content between headers
    sections = []
    for i, (section_start, section_name) in enumerate(all_matches):
        # Find end of this section (start of next section or end of doc)
        if i + 1 < len(all_matches):
            section_end = all_matches[i + 1][0]
        else:
            section_end = len(full_text)
        
        section_text = full_text[section_start:section_end].strip()
        
        # Find which pages this section spans
        page_nos = set()
        for start, end, page_no in page_mapping:
            if start < section_end and end > section_start:
                page_nos.add(page_no)
        
        if section_text and len(section_text) > 20:  # Skip very short sections (likely just artifacts)
            sections.append({
                "section_name": section_name,
                "text": section_text,
                "page_nos": sorted(list(page_nos))
            })
            logger.debug(f"Section '{section_name}' has {len(section_text)} chars")
    
    # If no sections found, return entire document as one section
    if not sections:
        logger.warning("No standard sections found, returning entire document as single section")
        all_page_nos = [page.get("page_no", 0) for page in pages]
        sections.append({
            "section_name": "Document",
            "text": full_text,
            "page_nos": sorted(all_page_nos)
        })
    
    return sections
