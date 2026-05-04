"""
Tender evaluation routes - main evaluation pipeline.
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException
from pathlib import Path
from backend.config import settings
from backend.database.db import get_db
from backend.database.models import Tender, Bidder, CriterionRecord
from backend.database.crud import get_criteria_for_tender, create_verdict
from backend.extraction.schemas import BidderValue, Criterion
from backend.ingestion.detector import detect_doc_type
from backend.ingestion.pdf_extractor import extract_digital_pdf
from backend.ingestion.ocr_engine import extract_with_ocr
from backend.extraction.ner_extractor import extract_entities
from backend.extraction.value_normaliser import normalise_currency, normalise_date
from backend.matching.rule_engine import apply_rule
from backend.matching.semantic_matcher import match_qualitative
from backend.verdict.generator import generate_verdict
from backend.verdict.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluate", tags=["evaluation"])


@router.post("/")
async def evaluate(tender_id: str, bidder_id: str):
    """
    Run evaluation for a bidder against all tender criteria.
    
    Args:
        tender_id: ID of the tender
        bidder_id: ID of the bidder
        
    Returns:
        List of verdict objects for all criteria
    """
    try:
        db = get_db()
        
        # Verify tender and bidder exist
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
        
        if not tender or not bidder:
            raise HTTPException(status_code=404, detail="Tender or bidder not found")
        
        # Get all criteria for tender
        criterion_records = get_criteria_for_tender(db, tender_id)
        if not criterion_records:
            raise HTTPException(status_code=400, detail="No criteria found for tender")
        
        # Get bidder documents
        bidder_dir = settings.data_dir / "uploads" / tender_id / bidder_id
        if not bidder_dir.exists():
            raise HTTPException(status_code=400, detail="No bidder documents found")
        
        # Extract content from all bidder documents
        bidder_content = {}
        for doc_file in bidder_dir.glob("*"):
            if doc_file.is_file():
                doc_type = detect_doc_type(str(doc_file))
                try:
                    if doc_type == "DIGITAL_PDF":
                        pages = extract_digital_pdf(str(doc_file))
                    else:
                        pages = extract_with_ocr(str(doc_file))
                    
                    bidder_content[doc_file.name] = {
                        "type": doc_type,
                        "pages": pages,
                        "full_text": "\n".join([p.get("text", "") for p in pages])
                    }
                except Exception as e:
                    logger.warning(f"Could not extract from {doc_file.name}: {e}")
        
        if not bidder_content:
            raise HTTPException(status_code=400, detail="Could not extract content from bidder documents")
        
        # Evaluate each criterion
        all_verdicts = []
        audit_logger = get_audit_logger()
        
        for criterion_record in criterion_records:
            try:
                # Reconstruct Criterion object
                criterion = Criterion(
                    criterion_id=criterion_record.id,
                    text=criterion_record.text,
                    criterion_type=criterion_record.criterion_type,
                    mandatory=criterion_record.mandatory,
                    threshold=criterion_record.threshold,
                    operator=criterion_record.operator,
                    unit=criterion_record.unit,
                    evidence_docs=[],
                    source_section="Tender",
                    source_text=criterion_record.text
                )
                
                # Combine all bidder text as context
                full_context = "\n".join([content["full_text"] for content in bidder_content.values()])
                
                # Extract entities and values from bidder documents
                entities = extract_entities(full_context)
                
                # Try to find matching value based on criterion type
                bidder_value = None
                
                if criterion.criterion_type == "financial":
                    # Look for monetary values
                    for entity in entities.get("TURNOVER", []):
                        normalised = normalise_currency(entity)
                        if normalised:
                            bidder_value = BidderValue(
                                criterion_id=criterion.criterion_id,
                                bidder_id=bidder_id,
                                extracted_value=entity,
                                normalised_value=normalised,
                                source_document=list(bidder_content.keys())[0],
                                source_page=1,
                                extraction_method="ner",
                                ocr_confidence=0.85
                            )
                            break
                
                elif criterion.criterion_type == "compliance":
                    # Look for dates and certificates
                    if any(keyword in criterion.text.lower() for keyword in ["iso", "cert", "date", "valid"]):
                        for entity in entities.get("ISO_CERT", []):
                            bidder_value = BidderValue(
                                criterion_id=criterion.criterion_id,
                                bidder_id=bidder_id,
                                extracted_value=entity,
                                normalised_value=None,
                                source_document=list(bidder_content.keys())[0],
                                source_page=1,
                                extraction_method="ner",
                                ocr_confidence=0.85
                            )
                            break
                
                elif criterion.criterion_type == "document":
                    # Check if document type is present
                    bidder_value = BidderValue(
                        criterion_id=criterion.criterion_id,
                        bidder_id=bidder_id,
                        extracted_value="document_provided" if bidder_content else "not_found",
                        normalised_value=None,
                        source_document=list(bidder_content.keys())[0] if bidder_content else "unknown",
                        source_page=1,
                        extraction_method="document_check",
                        ocr_confidence=1.0
                    )
                
                # If no value extracted, create placeholder
                if not bidder_value:
                    bidder_value = BidderValue(
                        criterion_id=criterion.criterion_id,
                        bidder_id=bidder_id,
                        extracted_value="not_extracted",
                        normalised_value=None,
                        source_document=list(bidder_content.keys())[0] if bidder_content else "unknown",
                        source_page=1,
                        extraction_method="extraction_failed",
                        ocr_confidence=0.0
                    )
                
                # Generate verdict
                verdict = generate_verdict(criterion, bidder_value, full_context, bidder_id)
                all_verdicts.append(verdict)
                
                # Log to audit trail
                audit_logger.log(verdict, tender_id, bidder_id)
                
                # Store in database
                create_verdict(db, verdict, tender_id)
                
            except Exception as e:
                logger.error(f"Error evaluating criterion {criterion_record.id}: {e}")
                raise
        
        logger.info(f"Evaluation complete for {bidder_id} on tender {tender_id}")
        
        return {
            "tender_id": tender_id,
            "bidder_id": bidder_id,
            "verdicts_count": len(all_verdicts),
            "verdicts": [
                {
                    "criterion_id": v.criterion_id,
                    "verdict": v.verdict,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning
                }
                for v in all_verdicts
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
