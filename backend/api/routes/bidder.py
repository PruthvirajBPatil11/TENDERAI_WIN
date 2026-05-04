"""
Bidder document upload routes.
"""

import logging
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from backend.config import settings
from backend.ingestion.detector import detect_doc_type
from backend.ingestion.pdf_extractor import extract_digital_pdf
from backend.ingestion.ocr_engine import extract_with_ocr
from backend.database.db import get_db
from backend.database.crud import create_bidder
from backend.database.models import Tender

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bidder", tags=["bidder"])


@router.post("/upload")
async def upload_bidder(tender_id: str, bidder_name: str, files: list[UploadFile] = File(...)):
    """
    Upload bidder submission documents.
    
    Args:
        tender_id: ID of the tender
        bidder_name: Name of the bidder
        files: List of submission files
        
    Returns:
        dict with bidder_id and file processing details
    """
    try:
        # Verify tender exists
        db = get_db()
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        # Generate bidder ID
        bidder_id = f"B{uuid.uuid4().hex[:8].upper()}"
        
        # Create bidder record
        create_bidder(db, bidder_id, tender_id, bidder_name)
        
        # Create bidder directory
        bidder_dir = settings.data_dir / "uploads" / tender_id / bidder_id
        bidder_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created bidder {bidder_id} for tender {tender_id}")
        
        # Process files
        file_results = []
        for file in files:
            try:
                # Save file
                file_path = bidder_dir / file.filename
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # Detect type
                doc_type = detect_doc_type(str(file_path))
                
                # Extract content (validate file is readable)
                if doc_type == "DIGITAL_PDF":
                    pages = extract_digital_pdf(str(file_path))
                else:
                    pages = extract_with_ocr(str(file_path))
                
                file_results.append({
                    "filename": file.filename,
                    "doc_type": doc_type,
                    "pages_extracted": len(pages),
                    "status": "uploaded"
                })
                
                logger.info(f"Processed {file.filename} for bidder {bidder_id}")
            
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                file_results.append({
                    "filename": file.filename,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "bidder_id": bidder_id,
            "bidder_name": bidder_name,
            "tender_id": tender_id,
            "files_count": len(files),
            "files": file_results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading bidder documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
