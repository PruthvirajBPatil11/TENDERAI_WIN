"""
OCR engine for extracting text from documents.

Routing strategy:
- Clean digital PDFs   -> pdfplumber  (fast, perfect, no API needed)
- Scanned PDFs/images  -> Gemini Vision (accurate, handles any quality)

PaddleOCR is not used — incompatible with Python 3.13+.
Gemini Vision is more capable for government document understanding.
"""

import json
import logging
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

from backend.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# HELPER: Detect if PDF is scanned or digital
# ─────────────────────────────────────────────────────────

def _is_scanned_pdf(filepath: str) -> bool:
    """
    Detect if a PDF is scanned by checking extractable word count.
    Less than 20 words per page on average = scanned.
    """
    try:
        with pdfplumber.open(filepath) as pdf:
            pages_to_check = min(3, len(pdf.pages))
            total_words = 0
            for page in pdf.pages[:pages_to_check]:
                text = page.extract_text() or ""
                total_words += len(text.split())
            avg = total_words / pages_to_check if pages_to_check > 0 else 0
            return avg < 20
    except Exception:
        return True


# ─────────────────────────────────────────────────────────
# METHOD 1: pdfplumber for clean digital PDFs
# ─────────────────────────────────────────────────────────

def _extract_with_pdfplumber(filepath: str) -> list:
    """
    Extract text from a clean digital PDF using pdfplumber.
    Returns confidence 0.99 — direct text extraction, no OCR needed.
    """
    pages = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                words = text.split()
                pages.append({
                    "page_no": i,
                    "text": text,
                    "words": [
                        {"word": w, "confidence": 0.99, "bbox": []}
                        for w in words
                    ],
                    "avg_confidence": 0.99,
                    "low_confidence": False,
                    "gemini_fallback": None,
                    "extraction_method": "pdfplumber"
                })
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")

    return pages


# ─────────────────────────────────────────────────────────
# METHOD 2: Gemini Vision for scanned docs and images
# ─────────────────────────────────────────────────────────

def extract_with_gemini_vision(image_path: str) -> dict:
    """
    Use Gemini Vision to extract text from scanned documents and images.

    Handles: scanned PDFs, JPG photos, PNG images, certificates with stamps.
    Returns structured dict with full text and key financial fields extracted.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)

        image_path_obj = Path(image_path)
        ext = image_path_obj.suffix.lower()
        mime_map = {
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png":  "image/png",
            ".pdf":  "application/pdf",
            ".bmp":  "image/bmp",
            ".tiff": "image/tiff",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        with open(image_path, "rb") as f:
            image_data = f.read()

        prompt = """You are a document OCR specialist for Indian government procurement.
Extract ALL text from this document image with maximum accuracy.

Pay special attention to:
- Rupee amounts (Rs., INR, crore, lakh, ₹)
- Dates in any format (DD/MM/YYYY, Month YYYY etc)
- Registration numbers (GST: 15 chars, PAN: 10 chars, ISO cert numbers)
- Company/organisation names
- Project names and contract numbers
- Validity/expiry dates of certificates

Return ONLY valid JSON, no markdown, no explanation:
{
  "full_text": "complete verbatim text from the document",
  "key_fields": {
    "amounts": ["every rupee amount found e.g. Rs. 8,20,00,000"],
    "dates": ["every date found e.g. 15/05/2024"],
    "registration_numbers": ["GST numbers, PAN, ISO cert numbers"],
    "company_name": "primary company or organisation name",
    "project_names": ["any project or work names mentioned"]
  },
  "confidence_note": "note any text that was unclear or unreadable"
}"""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt
            ]
        )

        raw = response.text.strip()

        # Strip markdown code blocks if present
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        logger.info(f"Gemini Vision extracted {len(result.get('full_text',''))} chars")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON: {e}")
        # Try to salvage plain text response
        try:
            return {
                "full_text": response.text,
                "key_fields": {},
                "confidence_note": "JSON parse failed — raw text returned"
            }
        except Exception:
            return {"full_text": "", "key_fields": {}, "confidence_note": str(e)}

    except Exception as e:
        logger.error(f"Gemini vision extraction failed: {e}")
        return {
            "full_text": "",
            "key_fields": {},
            "confidence_note": f"Extraction failed: {e}"
        }


def _extract_scanned_pdf_with_gemini(filepath: str) -> list:
    """Extract pages from a scanned PDF using Gemini Vision page by page."""
    pages = []
    try:
        doc = fitz.open(filepath)
        for page_no, page in enumerate(doc, start=1):
            # Render page to PNG in memory
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            png_bytes = pix.tobytes("png")

            # Save temp PNG and send to Gemini
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(
                suffix=".png", delete=False
            ) as tmp:
                tmp.write(png_bytes)
                tmp_path = tmp.name

            try:
                gemini_result = extract_with_gemini_vision(tmp_path)
                text = gemini_result.get("full_text", "")
                confidence = 0.82 if text.strip() else 0.0
                low_confidence = confidence < settings.ocr_confidence_threshold

                pages.append({
                    "page_no": page_no,
                    "text": text,
                    "words": [
                        {"word": w, "confidence": confidence, "bbox": []}
                        for w in text.split()
                    ],
                    "avg_confidence": confidence,
                    "low_confidence": low_confidence,
                    "gemini_fallback": gemini_result,
                    "extraction_method": "gemini_vision"
                })
            finally:
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Scanned PDF extraction failed: {e}")

    return pages


# ─────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────

def extract_with_ocr(filepath: str) -> list:
    """
    Smart document extractor — routes to best method automatically.

    Clean PDF  -> pdfplumber  (confidence 0.99, instant)
    Scanned PDF-> Gemini Vision per page (confidence ~0.82)
    Image file -> Gemini Vision directly (confidence ~0.82)

    Args:
        filepath: Path to PDF, JPG, PNG, or other document file

    Returns:
        List of page dicts with text, confidence, and metadata
    """
    filepath_str = str(filepath)
    ext = Path(filepath_str).suffix.lower()

    logger.info(f"Processing: {filepath_str}")

    # Route 1: Clean digital PDF -> pdfplumber
    if ext == ".pdf" and not _is_scanned_pdf(filepath_str):
        logger.info("Route: clean PDF -> pdfplumber")
        return _extract_with_pdfplumber(filepath_str)

    # Route 2: Scanned PDF -> Gemini Vision per page
    if ext == ".pdf":
        logger.info("Route: scanned PDF -> Gemini Vision")
        return _extract_scanned_pdf_with_gemini(filepath_str)

    # Route 3: Image file -> Gemini Vision directly
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        logger.info("Route: image file -> Gemini Vision")
        gemini_result = extract_with_gemini_vision(filepath_str)
        text = gemini_result.get("full_text", "")
        confidence = 0.82 if text.strip() else 0.0
        low_confidence = confidence < settings.ocr_confidence_threshold

        return [{
            "page_no": 1,
            "text": text,
            "words": [
                {"word": w, "confidence": confidence, "bbox": []}
                for w in text.split()
            ],
            "avg_confidence": confidence,
            "low_confidence": low_confidence,
            "gemini_fallback": gemini_result,
            "extraction_method": "gemini_vision"
        }]

    logger.warning(f"Unsupported file type: {ext}")
    return []
