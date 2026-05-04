"""
Financial table extraction using Camelot and Gemini vision API.
"""

import json
import logging
import re
from pathlib import Path
import cv2
import base64
from google.genai import Client
from backend.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini client at module level
_genai_client = Client(api_key=settings.gemini_api_key)


def clean_json(text: str) -> str:
    """Remove markdown and control characters from JSON text."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"```[a-zA-Z]*", "", text)
        text = text.replace("```", "").strip()
    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    return text


def safe_parse_json(text: str):
    """Robustly parse JSON with auto-fixes for common LLM issues."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt auto-fix for common LLM issues
        text = clean_json(text)
        # Fix trailing commas
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)
        try:
            return json.loads(text)
        except Exception as e:
            logger.error(f"Still failed parsing JSON: {e}")
            logger.debug(f"Cleaned response: {text}")
            return []


def extract_financial_table(filepath: str, page_no: int) -> list[dict]:
    """
    Extract financial tables from a specific page using Camelot or Gemini vision.
    
    Uses Camelot first for PDFs (structural extraction), then falls back to 
    Gemini vision API for scanned/image-based documents.
    
    Args:
        filepath: Path to the PDF or image file
        page_no: Page number (1-indexed)
        
    Returns:
        List of dict with keys: headers (list), rows (list of lists), source (str)
    """
    tables = []
    
    try:
        # Try camelot first for PDFs
        if filepath.lower().endswith('.pdf'):
            try:
                import camelot
                
                camelot_tables = camelot.read_pdf(
                    filepath,
                    pages=str(page_no),
                    flavor='stream'
                )
                
                if camelot_tables:
                    for table in camelot_tables:
                        df = table.df
                        if not df.empty:
                            headers = df.iloc[0].tolist() if len(df) > 0 else []
                            rows = [row.tolist() for _, row in df.iloc[1:].iterrows()]
                            
                            tables.append({
                                "headers": headers,
                                "rows": rows,
                                "source": "camelot"
                            })
                
                if tables:
                    return tables
            except Exception as e:
                logger.debug(f"Camelot extraction failed: {e}. Trying Gemini vision...")
        
        # Fallback: Gemini vision API
        # Extract page image and send to Gemini
        image_data = _extract_page_image(filepath, page_no)
        if image_data:
            message = _genai_client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    {
                        "text": """Extract all financial tables from this image. Return a JSON array where each element is a table:
[
  {
    "headers": ["Column1", "Column2"],
    "rows": [["value1", "value2"], ["value3", "value4"]]
  }
]
Return only valid JSON, no additional text."""
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            )
            
            response_text = message.text
            
            # Strip markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                start_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("```"):
                        start_idx = i + 1
                        break
                end_idx = len(lines)
                for i in range(start_idx, len(lines)):
                    if lines[i].startswith("```"):
                        end_idx = i
                        break
                response_text = "\n".join(lines[start_idx:end_idx])
            
            tables = safe_parse_json(response_text)
            
            # Add source metadata
            for table in tables:
                table["source"] = "gemini_vision"
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error extracting table from page {page_no}: {e}")
    except Exception as e:
        logger.error(f"Error extracting financial table from page {page_no}: {e}")
    
    return tables


def _extract_page_image(filepath: str, page_no: int) -> str | None:
    """
    Extract a page as PNG image and return as base64-encoded string.
    
    Args:
        filepath: Path to the file
        page_no: Page number (1-indexed)
        
    Returns:
        Base64-encoded PNG image string or None on error
    """
    try:
        if filepath.lower().endswith('.pdf'):
            import fitz
            
            doc = fitz.open(filepath)
            if page_no - 1 < len(doc):
                page = doc[page_no - 1]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                image_bytes = pix.tobytes("png")
                doc.close()
            else:
                return None
        else:
            # Load image directly
            img = cv2.imread(filepath)
            if img is None:
                return None
            _, image_bytes = cv2.imencode('.png', img)
            image_bytes = image_bytes.tobytes()
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    except Exception as e:
        logger.warning(f"Error extracting page image: {e}")
        return None

