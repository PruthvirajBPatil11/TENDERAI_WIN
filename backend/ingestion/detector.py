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
    
    For PDFs, analyzes text density to distinguish between digital and scanned documents.
    Digital PDFs have extractable text via pdfplumber.
    Scanned PDFs have minimal text (OCR-only content).
    
    Args:
        filepath: Path to the document file
        
    Returns:
        One of: "DIGITAL_PDF", "SCANNED_PDF", "IMAGE", "DOCX"
    """
    try:
        path = Path(filepath)
        
        # Check extension
        suffix = path.suffix.lower()
        
        if suffix == ".docx":
            logger.info(f"Detected DOCX: {filepath}")
            return "DOCX"
        
        if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
            logger.info(f"Detected IMAGE: {filepath}")
            return "IMAGE"
        
        if suffix == ".pdf":
            try:
                with pdfplumber.open(filepath) as pdf:
                    # Sample first 3 pages to determine type
                    total_words = 0
                    pages_sampled = 0
                    
                    for page in pdf.pages[:3]:
                        extracted_text = page.extract_text()
                        if extracted_text:
                            total_words += len(extracted_text.split())
                            pages_sampled += 1
                    
                    if pages_sampled == 0:
                        logger.info(f"Detected SCANNED_PDF (no extractable text): {filepath}")
                        return "SCANNED_PDF"
                    
                    # Calculate average words per page
                    avg_words_per_page = total_words / pages_sampled
                    
                    # Threshold: if avg < 3 words per page, likely scanned
                    if avg_words_per_page < 3:
                        logger.info(f"Detected SCANNED_PDF (avg {avg_words_per_page:.1f} words/page): {filepath}")
                        return "SCANNED_PDF"
                    else:
                        logger.info(f"Detected DIGITAL_PDF (avg {avg_words_per_page:.1f} words/page): {filepath}")
                        return "DIGITAL_PDF"
            
            except Exception as pdf_error:
                logger.warning(f"Error analyzing PDF {filepath}: {pdf_error}. Defaulting to DIGITAL_PDF")
                return "DIGITAL_PDF"
        
        # Default fallback
        logger.warning(f"Unknown file type for {filepath}, defaulting to DIGITAL_PDF")
        return "DIGITAL_PDF"
    
    except Exception as e:
        logger.error(f"Error in detect_doc_type for {filepath}: {e}. Defaulting to DIGITAL_PDF")
        return "DIGITAL_PDF"
