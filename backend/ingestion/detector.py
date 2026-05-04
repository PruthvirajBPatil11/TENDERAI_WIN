"""
Document type detector - identifies whether a document is a digital PDF, scanned PDF, image, or DOCX.
"""

import logging
from pathlib import Path
import pdfplumber

logger = logging.getLogger(__name__)


def detect_doc_type(filepath: str) -> str:
    """
    Detect the document type based on file extension and content analysis.
    
    Args:
        filepath: Path to the document file
        
    Returns:
        One of: "DIGITAL_PDF", "SCANNED_PDF", "IMAGE", "DOCX"
    """
    path = Path(filepath)
    
    # Check extension
    suffix = path.suffix.lower()
    
    if suffix == ".docx":
        return "DOCX"
    
    if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]:
        return "IMAGE"
    
    if suffix == ".pdf":
        try:
            with pdfplumber.open(filepath) as pdf:
                # Sample first 3 pages to determine type
                total_words = 0
                pages_sampled = 0
                
                for page_num, page in enumerate(pdf.pages[:3]):
                    if page.extract_text():
                        total_words += len(page.extract_text().split())
                        pages_sampled += 1
                
                if pages_sampled == 0:
                    return "SCANNED_PDF"
                
                # Calculate average words per page
                avg_words_per_page = total_words / pages_sampled
                
                # If average < 20 words per page, likely a scanned PDF
                if avg_words_per_page < 20:
                    return "SCANNED_PDF"
                else:
                    return "DIGITAL_PDF"
        except Exception as e:
            logger.warning(f"Error analyzing PDF {filepath}: {e}. Defaulting to SCANNED_PDF.")
            return "SCANNED_PDF"
    
    # Default fallback
    logger.warning(f"Unknown file type for {filepath}. Defaulting to IMAGE.")
    return "IMAGE"
