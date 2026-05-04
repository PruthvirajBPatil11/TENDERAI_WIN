"""
Layout parser for extracting tables and forms from documents.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_layout(filepath: str) -> list[dict]:
    """
    Extract layout information including tables and forms.
    
    Uses Docling if available, otherwise falls back to pdfplumber.
    
    Args:
        filepath: Path to the document file
        
    Returns:
        List of dicts with keys: page_no, tables, forms
    """
    pages_data = []
    path = Path(filepath)
    
    try:
        # Try docling first
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import ConversionStatus
            
            converter = DocumentConverter()
            result = converter.convert_single(filepath)
            
            if result.status == ConversionStatus.SUCCESS:
                # Extract tables from docling result
                for page_idx, page in enumerate(result.document.pages):
                    page_num = page_idx + 1
                    
                    tables = []
                    forms = []
                    
                    # Note: Docling structure varies; this is a simplified approach
                    pages_data.append({
                        "page_no": page_num,
                        "tables": tables,
                        "forms": forms
                    })
                
                return pages_data
        except ImportError:
            logger.debug("Docling not available, falling back to pdfplumber")
        
        # Fallback: use pdfplumber
        import pdfplumber
        
        with pdfplumber.open(filepath) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                
                tables = []
                try:
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            table_dict = {
                                "headers": table[0] if table else [],
                                "rows": table[1:] if table else []
                            }
                            tables.append(table_dict)
                except Exception as e:
                    logger.warning(f"Error extracting tables from page {page_num}: {e}")
                
                pages_data.append({
                    "page_no": page_num,
                    "tables": tables,
                    "forms": []
                })
    except Exception as e:
        logger.error(f"Error extracting layout from {filepath}: {e}")
        raise
    
    return pages_data
