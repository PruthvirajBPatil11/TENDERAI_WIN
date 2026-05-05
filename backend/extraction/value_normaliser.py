"""
Value normalisation - converts various currency, date, and numeric formats to standard forms.
"""

import logging
import re
from datetime import datetime

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
        text = str(text).strip()
        
        # Step 1: Remove currency symbols (carefully to preserve decimal point)
        text = re.sub(r'Rs\.?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'INR\s*', '', text, flags=re.IGNORECASE)
        text = text.replace('₹', '')
        text = text.strip()
        
        # Step 2: Extract number and unit
        # Pattern: number (digits, commas, decimals) + optional space + optional unit
        match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:(crore|cr|Cr\.|Cr|CRORE|Crs|lakh|lac|L|Lakh|LAKH))?', text, re.IGNORECASE)
        
        if not match:
            return None
        
        # Extract the number part - remove commas and parse as float
        number_str = match.group(1).replace(',', '')
        number = float(number_str)
        
        # Extract the unit part if present
        unit = match.group(2) if match.group(2) else ""
        unit = unit.lower()
        
        # Step 3: Multiply by appropriate factor based on unit
        if unit and any(u in unit for u in ['crore', 'cr', 'crs']):
            number = number * 10_000_000
        elif unit and any(u in unit for u in ['lakh', 'lac', 'l']):
            number = number * 100_000
        
        return float(number)
    
    except Exception as e:
        logger.warning(f"Error normalizing currency '{text}': {e}")
        return None


def normalise_date(text: str) -> str | None:
    """
    Normalize date formats to YYYY-MM-DD.
    
    Accepts: DD/MM/YYYY, DD-MM-YYYY, D/M/YYYY, etc.
    
    Args:
        text: Date text to normalize
        
    Returns:
        Date in YYYY-MM-DD format, or None if parsing fails
    """
    if not text:
        return None
    
    try:
        text = str(text).strip()
        
        # Try various date patterns
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or D/M/YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                
                # Validate date ranges
                if 1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2030:
                    return f"{year:04d}-{month:02d}-{day:02d}"
        
        return None
    
    except Exception as e:
        logger.warning(f"Error normalizing date '{text}': {e}")
        return None


def is_date_valid(date_str: str) -> bool:
    """
    Check if a date is valid (after May 1, 2026 - the reference date).
    
    Args:
        date_str: Date string in any supported format
        
    Returns:
        True if date is after May 1, 2026, False otherwise
    """
    if not date_str:
        return False
    
    try:
        # Normalize the date first
        normalized = normalise_date(date_str)
        if not normalized:
            return False
        
        # Parse normalized date (YYYY-MM-DD)
        date_obj = datetime.strptime(normalized, "%Y-%m-%d").date()
        
        # Reference date: May 1, 2026
        reference_date = datetime(2026, 5, 1).date()
        
        # Valid if date is after reference date
        return date_obj > reference_date
    
    except Exception as e:
        logger.warning(f"Error validating date '{date_str}': {e}")
        return False
