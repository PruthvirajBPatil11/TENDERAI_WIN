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
    # Common section headers in government tenders
    section_patterns = [
        (r"(?:section\s*[-:]?\s*)?eligibility\s+criteria", "Eligibility Criteria"),
        (r"technical\s+(?:requirement|specification)s?", "Technical Requirements"),
        (r"financial\s+(?:requirement|qualification)s?", "Financial Requirements"),
        (r"scope\s+of\s+work", "Scope of Work"),
        (r"general\s+(?:condition|terms?)", "General Conditions"),
        (r"qualification\s+(?:requirement)?s?", "Qualifications"),
        (r"experience\s+requirement", "Experience Requirements"),
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
    
    # Find sections
    sections = []
    current_pos = 0
    
    for pattern, section_name in section_patterns:
        # Case-insensitive search
        matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
        
        for match in matches:
            section_start = match.start()
            
            # Find the next section or end of document
            next_section_start = len(full_text)
            for other_pattern, _ in section_patterns:
                for other_match in re.finditer(other_pattern, full_text[section_start + 1:], re.IGNORECASE):
                    next_section_start = min(next_section_start, section_start + 1 + other_match.start())
            
            section_text = full_text[section_start:next_section_start].strip()
            
            # Find which pages this section spans
            page_nos = set()
            for start, end, page_no in page_mapping:
                if start < next_section_start and end > section_start:
                    page_nos.add(page_no)
            
            if section_text:
                sections.append({
                    "section_name": section_name,
                    "text": section_text,
                    "page_nos": sorted(list(page_nos))
                })
    
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
