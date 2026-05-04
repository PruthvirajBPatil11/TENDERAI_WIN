"""
Tender document upload and processing routes.
"""

import logging
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from backend.config import settings
from backend.ingestion.detector import detect_doc_type
from backend.ingestion.pdf_extractor import extract_digital_pdf
from backend.ingestion.ocr_engine import extract_with_ocr
from backend.ingestion.chunker import chunk_document
from backend.extraction.section_classifier import classify_sections
from backend.extraction.criterion_extractor import extract_criteria
from backend.extraction.schemas import Criterion
from backend.database.db import get_db
from backend.database.crud import create_tender, create_criterion
from backend.vector_store.qdrant_client import store_criterion, init_collection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tender", tags=["tender"])


@router.post("/upload")
async def upload_tender(file: UploadFile = File(...)):
    """
    Upload and process a tender document.
    
    Returns:
        dict with tender_id and extracted criteria list
    """
    try:
        # Generate tender ID
        tender_id = f"T{uuid.uuid4().hex[:8].upper()}"
        
        # Save file
        upload_dir = settings.data_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Tender file uploaded: {file.filename}")
        
        # Detect document type
        doc_type = detect_doc_type(str(file_path))
        logger.info(f"Detected document type: {doc_type}")
        
        # Extract text based on type
        if doc_type == "DIGITAL_PDF":
            pages = extract_digital_pdf(str(file_path))
        else:
            pages = extract_with_ocr(str(file_path))
        
        logger.info(f"Extracted {len(pages)} pages from tender")
        
        # Chunk document into sections
        sections = chunk_document(pages)
        logger.info(f"Chunked into {len(sections)} sections")
        
        # Classify sections
        sections = classify_sections(sections)
        logger.info(f"Section classification complete")
        
        # Log which sections were classified as eligibility
        eligibility_sections = [s for s in sections if s.get("is_eligibility_section", False)]
        logger.info(f"Found {len(eligibility_sections)} eligibility sections out of {len(sections)} total sections")
        for i, s in enumerate(eligibility_sections):
            logger.info(f"  Eligibility section {i+1}: '{s.get('section_name', 'Unknown')}'")
        
        # Extract criteria from eligibility sections
        all_criteria = []
        for section in sections:
            if section.get("is_eligibility_section", False):
                logger.info(f"Extracting criteria from: {section.get('section_name', 'Unknown')}")
                criteria = extract_criteria(section["text"], section["section_name"])
                logger.info(f"  Extracted {len(criteria)} criteria from this section")
                all_criteria.extend(criteria)
        
        logger.info(f"Extracted {len(all_criteria)} criteria")
        
        # Store in database
        db = get_db()
        create_tender(db, tender_id, file.filename, str(file_path), doc_type)
        
        # Store criteria in database and vector store
        init_collection()
        for criterion in all_criteria:
            if not criterion.criterion_id.startswith("C"):
                criterion.criterion_id = f"C{len(all_criteria):03d}"
            create_criterion(db, criterion, tender_id)
            store_criterion(criterion)
        
        # Return response
        return {
            "tender_id": tender_id,
            "doc_type": doc_type,
            "criteria_count": len(all_criteria),
            "sections_analyzed": len(sections),
            "eligibility_sections_found": len(eligibility_sections),
            "criteria": [
                {
                    "id": c.criterion_id,
                    "text": c.text,
                    "type": c.criterion_type,
                    "mandatory": c.mandatory,
                    "threshold": c.threshold,
                    "operator": c.operator,
                    "unit": c.unit
                }
                for c in all_criteria
            ]
        }
    
    except Exception as e:
        logger.error(f"Error uploading tender: {e}")
        raise HTTPException(status_code=500, detail=str(e))
