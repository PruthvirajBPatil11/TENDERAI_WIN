"""
Named Entity Recognition for extracting specific entities like GST, PAN, dates, amounts.
"""

import logging
import re
import spacy
from typing import Dict, List

logger = logging.getLogger(__name__)

# Load spaCy model globally
_nlp = None


def get_nlp_model():
    """Load spaCy English model if not already loaded."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_lg")
        except OSError:
            logger.warning("en_core_web_lg not found. Install with: python -m spacy download en_core_web_lg")
            _nlp = spacy.blank("en")
    return _nlp


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities and specific patterns from text.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        Dict with entity types as keys and list of extracted values
    """
    entities = {
        "TURNOVER": [],
        "GST_NO": [],
        "PAN_NO": [],
        "ISO_CERT": [],
        "VALID_DATE": [],
        "PROJECT_VALUE": [],
    }
    
    # Pattern definitions
    patterns = {
        "TURNOVER": [
            r"₹?\s*(\d+(?:\.\d+)?)\s*(?:crore|cr|Cr|CRORE)",
            r"Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|cr|Cr|CRORE)",
            r"(\d+(?:\.\d+)?)\s*crore\s*(?:turnover|revenue|annual)",
        ],
        "GST_NO": [
            r"([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1})",
        ],
        "PAN_NO": [
            r"([A-Z]{5}[0-9]{4}[A-Z]{1})",
        ],
        "ISO_CERT": [
            r"ISO\s*9001(?::?2015)?",
            r"ISO\s*14001(?::?2015)?",
            r"ISO\s*45001",
        ],
        "VALID_DATE": [
            r"(?:valid\s+till|validity|expiry)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ],
        "PROJECT_VALUE": [
            r"(?:project|contract)\s+value\s*[:\-]?\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|lakh|lac)",
        ],
    }
    
    # Apply regex patterns
    for entity_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.group(0) not in entities[entity_type]:
                    entities[entity_type].append(match.group(0))
    
    # Use spaCy for additional entity recognition
    try:
        nlp = get_nlp_model()
        doc = nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "DATE" and "VALID_DATE" not in entities:
                entities["VALID_DATE"].append(ent.text)
            elif ent.label_ == "MONEY":
                entities["PROJECT_VALUE"].append(ent.text)
    except Exception as e:
        logger.debug(f"Error in spaCy NER: {e}")
    
    return entities
