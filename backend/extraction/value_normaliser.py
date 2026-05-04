"""
Value normalisation - converts various currency, date, and numeric formats to standard forms.
"""

import logging
import re
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def normalise_currency(text: str) -> float | None:
    """
    Convert various Indian currency formats to rupees as float.
    
    Handles: ₹5 crore, Rs. 5,23,45,000, 5.23 crore, 52.35 lakh, INR 5000000, 5 Cr, 500 L
    
    Args:
        text: Currency text to normalize
        
    Returns:
        Value in rupees as float, or None if parsing fails
    """
    if not text:
        return None
    
    try:
        # Clean the text
        text = text.strip()
        
        # Remove currency symbols and abbreviations to extract number and unit
        # Pattern: number (with optional decimals and commas) followed by optional unit
        patterns = [
            # Format: ₹X crore, Rs. X crore, INR X crore
            (r'[₹Rs.\s]*\s*(\d+(?:[,\.]\d+)*)\s*(?:crore|cr|Cr|CRORE|Crs)', lambda m: float(m.group(1).replace(',', '')) * 10000000),
            # Format: X lakh, X lac
            (r'[₹Rs.\s]*\s*(\d+(?:[,\.]\d+)*)\s*(?:lakh|lac|L|Lakh)', lambda m: float(m.group(1).replace(',', '')) * 100000),
            # Format: plain number (assume rupees)
            (r'[₹Rs.\s]*\s*(\d+(?:[,\.]\d+)*)', lambda m: float(m.group(1).replace(',', ''))),
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return converter(match)
        
        return None
    except Exception as e:
        logger.warning(f"Error normalizing currency '{text}': {e}")
        return None


def normalise_date(text: str) -> str | None:
    """
    Parse date in various formats and return ISO format YYYY-MM-DD.
    
    Handles: DD/MM/YYYY, DD-MM-YYYY, Month DD YYYY, DD Month YYYY
    
    Args:
        text: Date text to normalize
        
    Returns:
        ISO format date string (YYYY-MM-DD) or None if parsing fails
    """
    if not text:
        return None
    
    try:
        # Try to parse the date
        parsed_date = date_parser.parse(text, dayfirst=True)
        return parsed_date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Error normalizing date '{text}': {e}")
        return None


def is_date_valid(date_str: str) -> bool:
    """
    Check if a date is valid (in the future).
    
    Args:
        date_str: Date string in ISO format (YYYY-MM-DD) or other recognizable format
        
    Returns:
        True if date is in the future, False otherwise
    """
    if not date_str:
        return False
    
    try:
        # Parse the date
        parsed_date = date_parser.parse(date_str, dayfirst=True)
        
        # Compare with today
        today = datetime.now().date()
        return parsed_date.date() > today
    except Exception as e:
        logger.warning(f"Error validating date '{date_str}': {e}")
        return False
