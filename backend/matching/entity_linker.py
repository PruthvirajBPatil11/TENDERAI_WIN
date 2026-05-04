"""
Entity linker - fuzzy matching for company names and entities.
"""

import logging
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


def match_company_name(name_in_doc: str, registered_name: str) -> tuple[bool, float]:
    """
    Match company name in document against registered name using fuzzy matching.
    
    Args:
        name_in_doc: Company name as it appears in document
        registered_name: Officially registered company name
        
    Returns:
        Tuple of (is_match: bool, score: float)
        - If score > 85: (True, score)
        - If 70-85: (True, score) with warning logged
        - If < 70: (False, score)
    """
    if not name_in_doc or not registered_name:
        return (False, 0.0)
    
    # Normalize names
    name1 = name_in_doc.lower().strip()
    name2 = registered_name.lower().strip()
    
    # Use token sort ratio for robustness against word order variations
    score = fuzz.token_sort_ratio(name1, name2)
    
    if score > 85:
        return (True, score)
    elif 70 <= score <= 85:
        logger.warning(f"Partial company name match: '{name_in_doc}' vs '{registered_name}' (score: {score})")
        return (True, score)
    else:
        logger.debug(f"Company name mismatch: '{name_in_doc}' vs '{registered_name}' (score: {score})")
        return (False, score)
