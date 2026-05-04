"""
Digital PDF extraction using pdfplumber.
"""

import logging
from pathlib import Path
import pdfplumber

logger = logging.getLogger(__name__)


def extract_digital_pdf(filepath: str) -> list[dict]:
    """
    Extract text and tables from a digital (text-based) PDF.
    
    Args:
        filepath: Path to the PDF file
        
    Returns:
        List of dicts with keys: page_no, text, tables, word_count
    """
    pages_data = []
    
    try:
        with pdfplumber.open(filepath) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                
                # Extract text
                text = page.extract_text() or ""
                
                # Extract tables
                tables = []
                try:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables = page_tables
                except Exception as e:
                    logger.warning(f"Error extracting tables from page {page_num}: {e}")
                
                # Count words
                word_count = len(text.split())
                
                pages_data.append({
                    "page_no": page_num,
                    "text": text,
                    "tables": tables,
                    "word_count": word_count
                })
    except Exception as e:
        logger.error(f"Error extracting digital PDF {filepath}: {e}")
        raise
    
    return pages_data
