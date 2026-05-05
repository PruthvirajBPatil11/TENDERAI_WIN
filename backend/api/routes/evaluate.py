"""
Tender evaluation routes - main evaluation pipeline.
Evaluates bidders against tender criteria using document routing and value extraction.

Endpoints:
- POST /evaluate - Run full evaluation for a bidder against all tender criteria
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import Tender, Bidder, CriterionRecord, BidderDocument, VerdictRecord
from backend.extraction.schemas import Criterion
from backend.verdict.generator import generate_verdict
from backend.verdict.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluate", tags=["evaluation"])


class EvaluateRequest(BaseModel):
    """Request body for evaluation endpoint."""
    tender_id: str
    bidder_id: str


@router.post("/")
async def evaluate(
    request: EvaluateRequest,
    db: Session = Depends(get_db)
):
    """
    Run evaluation for a bidder against all tender criteria.
    
    Pipeline:
    1. Verify tender and bidder exist in database
    2. Load all criteria for the tender
    3. Load all bidder documents from database
    4. Log comprehensive information about documents available
    5. For each criterion, call generate_verdict() with all documents
    6. Generate verdict using keyword-based document routing
    7. Store verdicts in database
    8. Log to audit trail
    9. Return list of verdict objects
    
    Args:
        request: EvaluateRequest with tender_id and bidder_id
        db: Database session
        
    Returns:
        Dict with evaluation results:
        {
            "tender_id": str,
            "bidder_id": str,
            "verdicts_count": int,
            "verdicts": [
                {
                    "criterion_id": str,
                    "verdict": "PASS" | "FAIL" | "MANUAL_REVIEW",
                    "confidence": float (0.0-1.0),
                    "reasoning": str,
                    "source_document": str,
                    "source_page": int,
                    "ocr_confidence": float (0.0-1.0),
                    "evidence_quote": str
                }
            ]
        }
    
    Raises:
        HTTPException 404: Tender or bidder not found
        HTTPException 400: No criteria found for tender
        HTTPException 500: Internal evaluation error
    
    Logs:
    - INFO: Start/complete of evaluation, document count, verdict results
    - DEBUG: Tender/bidder lookup, criterion processing
    - WARNING: Missing documents, evaluation errors
    """
    try:
        tender_id = request.tender_id
        bidder_id = request.bidder_id
        
        logger.info(f"Starting evaluation: tender={tender_id}, bidder={bidder_id}")
        
        # ===== STEP 1: Verify tender and bidder exist =====
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        if not tender:
            logger.error(f"Tender {tender_id} not found")
            raise HTTPException(status_code=404, detail=f"Tender {tender_id} not found")
        
        bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
        if not bidder:
            logger.error(f"Bidder {bidder_id} not found")
            raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} not found")
        
        logger.debug(f"Found tender: {tender.filename}, bidder: {bidder.name}")
        
        # ===== STEP 2: Load ALL criteria for tender =====
        criterion_records = db.query(CriterionRecord).filter(
            CriterionRecord.tender_id == tender_id
        ).all()
        
        if not criterion_records:
            logger.error(f"No criteria found for tender {tender_id}")
            raise HTTPException(status_code=400, detail=f"No criteria found for tender {tender_id}")
        
        logger.info(f"Loaded {len(criterion_records)} criteria for tender {tender_id}")
        
        # ===== STEP 3: Load ALL bidder documents from database =====
        doc_records = db.query(BidderDocument).filter(
            BidderDocument.bidder_id == bidder_id
        ).all()
        
        if not doc_records:
            logger.error(f"No documents found for bidder {bidder_id}")
            raise HTTPException(status_code=404, detail=f"No documents found for bidder {bidder_id}")
        
        logger.info(f"Loaded {len(doc_records)} documents for bidder {bidder_id}")
        
        # ===== STEP 4: Convert DB records to dicts for generator =====
        # Each document dict must have: filename, doc_type, text, ocr_confidence, extraction_method
        bidder_docs = []
        for doc in doc_records:
            doc_dict = {
                "doc_id": doc.doc_id,
                "bidder_id": bidder_id,
                "filename": doc.filename,
                "doc_type": doc.doc_type,
                "text": doc.extracted_text or "",
                "ocr_confidence": doc.ocr_confidence or 0.99,
                "extraction_method": getattr(doc, "extraction_method", "unknown")
            }
            bidder_docs.append(doc_dict)
        
        # ===== STEP 5: Log all documents available BEFORE evaluation =====
        logger.info(f"Documents available for evaluation ({len(bidder_docs)}):")
        for i, d in enumerate(bidder_docs, 1):
            logger.info(
                f"  [{i}] {d['filename']}: "
                f"type={d['doc_type']}, "
                f"ocr_confidence={d['ocr_confidence']:.3f}, "
                f"text_length={len(d['text'])}, "
                f"extraction_method={d['extraction_method']}"
            )
        
        # ===== STEP 6: Evaluate each criterion against all documents =====
        all_verdicts = []
        audit_logger = get_audit_logger()
        verdict_records_to_add = []
        
        for i, criterion_record in enumerate(criterion_records, 1):
            try:
                logger.debug(f"Evaluating criterion [{i}/{len(criterion_records)}]: {criterion_record.id}")
                
                # Reconstruct Criterion object from database record
                criterion = Criterion(
                    criterion_id=criterion_record.id,
                    text=criterion_record.text,
                    criterion_type=criterion_record.criterion_type or "technical",
                    mandatory=criterion_record.mandatory or True,
                    threshold=criterion_record.threshold,
                    operator=criterion_record.operator,
                    unit=criterion_record.unit,
                    evidence_docs=getattr(criterion_record, 'evidence_docs', None) or [],
                    source_section="Tender",
                    source_text=criterion_record.text
                )
                
                # Generate verdict - passes ALL bidder documents to generator
                # Generator will use keyword scoring to find best document for this criterion
                verdict = generate_verdict(criterion, bidder_docs, bidder_id)
                all_verdicts.append(verdict)
                
                logger.info(
                    f"  Criterion {criterion_record.id}: {verdict.verdict} "
                    f"(confidence={verdict.confidence:.2f}, "
                    f"ocr={verdict.ocr_confidence:.3f}, "
                    f"source={verdict.source_document})"
                )
                
                # Prepare verdict record for database
                verdict_record = VerdictRecord(
                    id=f"{bidder_id}_{criterion_record.id}_{uuid_short()}",
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    criterion_id=criterion_record.id,
                    verdict=verdict.verdict,
                    confidence=verdict.confidence,
                    reasoning=verdict.reasoning,
                    source_document=verdict.source_document,
                    source_page=verdict.source_page,
                    verdict_hash=verdict.hash
                )
                verdict_records_to_add.append(verdict_record)
                
                # Log to audit trail
                try:
                    audit_logger.log(verdict, tender_id, bidder_id)
                except Exception as audit_error:
                    logger.warning(f"Could not log to audit trail: {audit_error}")
                
            except Exception as e:
                logger.error(
                    f"Error evaluating criterion {criterion_record.id}: {e}",
                    exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to evaluate criterion {criterion_record.id}: {str(e)}"
                )
        
        # ===== STEP 7: Store verdicts in database =====
        for verdict_record in verdict_records_to_add:
            db.add(verdict_record)
        
        db.commit()
        
        logger.info(
            f"Evaluation complete: tender={tender_id}, bidder={bidder_id}, "
            f"verdicts={len(all_verdicts)}"
        )
        
        # ===== STEP 8: Return results =====
        return {
            "tender_id": tender_id,
            "bidder_id": bidder_id,
            "verdicts_count": len(all_verdicts),
            "verdicts": [
                {
                    "criterion_id": v.criterion_id,
                    "verdict": v.verdict,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                    "source_document": v.source_document,
                    "source_page": v.source_page,
                    "ocr_confidence": v.ocr_confidence,
                    "evidence_quote": v.evidence_quote
                }
                for v in all_verdicts
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


def uuid_short() -> str:
    """Generate a short unique identifier."""
    return uuid.uuid4().hex[:8]

