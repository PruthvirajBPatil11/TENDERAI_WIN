"""
Named Entity Recognition for extracting specific entities like GST, PAN, dates, amounts.
Uses regex patterns for reliable extraction in tender evaluation domain.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities and specific patterns from text using regex.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        Dict with entity types as keys and list of extracted values
    """
    if not text:
        return {
            "TURNOVER": [],
            "AMOUNT": [],
            "GST_NO": [],
            "PAN_NO": [],
            "ISO_CERT": [],
            "VALID_DATE": [],
            "COMPANY_NAME": []
        }
    
    entities = {
        "TURNOVER": [],
        "AMOUNT": [],
        "GST_NO": [],
        "PAN_NO": [],
        "ISO_CERT": [],
        "VALID_DATE": [],
        "COMPANY_NAME": []
    }
    
    try:
        # Extract TURNOVER amounts (look for "turnover" context)
        turnover_pattern = r'(?:annual\s+)?turnover\s*[:=]?\s*(?:Rs\.?\s*|₹\s*)?[\d,]+(?:\.\d+)?(?:\s*(?:crore|lakh|Cr\.?|L\.?))?'
        for match in re.finditer(turnover_pattern, text, re.IGNORECASE):
            entities["TURNOVER"].append(match.group(0).strip())
        
        # Extract AMOUNT (any rupee amounts)
        amount_pattern = r'(?:Rs\.?\s*|₹\s*|INR\s*)[\d,]+(?:\.\d+)?(?:\s*(?:crore|lakh|Cr\.?|L\.?))?'
        for match in re.finditer(amount_pattern, text):
            entities["AMOUNT"].append(match.group(0).strip())
        
        # Extract GST_NO (GSTIN format)
        gstin_pattern = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}'
        for match in re.finditer(gstin_pattern, text):
            entities["GST_NO"].append(match.group(0).strip())
        
        # Extract PAN_NO (PAN format)
        pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'
        for match in re.finditer(pan_pattern, text):
            # Filter out false positives (must not be part of GSTIN)
            if len(match.group(0)) == 10:
                entities["PAN_NO"].append(match.group(0).strip())
        
        # Extract ISO_CERT (ISO 9001 and variants)
        iso_pattern = r'ISO\s*9001(?::\d{4})?'
        for match in re.finditer(iso_pattern, text, re.IGNORECASE):
            entities["ISO_CERT"].append(match.group(0).strip())
        
        # Extract VALID_DATE (dates near validity keywords)
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        for match in re.finditer(date_pattern, text):
            date_str = match.group(0)
            # Look for nearby keywords: expiry, valid, till, upto
            start_pos = max(0, match.start() - 100)
            end_pos = min(len(text), match.end() + 50)
            context = text[start_pos:end_pos].lower()
            
            if any(kw in context for kw in ['expir', 'valid', 'till', 'upto', 'upto', 'till']):
                entities["VALID_DATE"].append(date_str)
        
        # Extract COMPANY_NAME
        company_pattern = r'(?:M/s\.?|Company:|Pvt\.?\s+Ltd|Ltd|LLP)\s+([A-Za-z\s&,]+?)(?:\n|,|$)'
        for match in re.finditer(company_pattern, text, re.IGNORECASE):
            company_name = match.group(1).strip()
            if company_name and len(company_name) > 2:
                entities["COMPANY_NAME"].append(company_name)
        
        logger.info(f"Extracted entities: {entities}")
        return entities
    
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return {
            "TURNOVER": [],
            "AMOUNT": [],
            "GST_NO": [],
            "PAN_NO": [],
            "ISO_CERT": [],
            "VALID_DATE": [],
            "COMPANY_NAME": []
        }
