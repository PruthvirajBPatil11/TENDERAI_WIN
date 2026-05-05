"""
Report generation and retrieval routes.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from backend.config import settings
from backend.database.db import get_db
from backend.database.models import VerdictRecord, AuditLog
from backend.extraction.schemas import Verdict, BidderReport
from backend.verdict.report_builder import build_report
from backend.verdict.pdf_exporter import export_pdf
from backend.verdict.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/report", tags=["reports"])


@router.get("/{tender_id}/{bidder_id}")
async def get_report(tender_id: str, bidder_id: str):
    """
    Get evaluation report for a bidder.
    
    Returns:
        BidderReport JSON
    """
    try:
        db = get_db()
        
        # Get all verdicts for bidder
        verdict_records = db.query(VerdictRecord).filter(
            VerdictRecord.tender_id == tender_id,
            VerdictRecord.bidder_id == bidder_id
        ).all()
        
        if not verdict_records:
            raise HTTPException(status_code=404, detail="No verdicts found for bidder")
        
        # Convert to Verdict objects
        verdicts = []
        for vr in verdict_records:
            verdict = Verdict(
                criterion_id=vr.criterion_id,
                bidder_id=vr.bidder_id,
                verdict=vr.verdict,
                confidence=vr.confidence,
                reasoning=vr.reasoning,
                evidence_quote=vr.reasoning[:100] if vr.reasoning else None,
                source_document=vr.source_document or "unknown",
                source_page=vr.source_page or 1,
                hash=vr.verdict_hash if hasattr(vr, 'verdict_hash') and vr.verdict_hash else None
            )
            verdicts.append(verdict)
        
        # Build report
        report = build_report(tender_id, bidder_id, verdicts)
        
        return report.model_dump()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tender_id}/{bidder_id}/pdf")
async def get_report_pdf(tender_id: str, bidder_id: str):
    """
    Get evaluation report as PDF.
    
    Returns:
        PDF file
    """
    try:
        db = get_db()
        
        # Get all verdicts for bidder
        verdict_records = db.query(VerdictRecord).filter(
            VerdictRecord.tender_id == tender_id,
            VerdictRecord.bidder_id == bidder_id
        ).all()
        
        if not verdict_records:
            raise HTTPException(status_code=404, detail="No verdicts found for bidder")
        
        # Convert to Verdict objects
        verdicts = []
        for vr in verdict_records:
            verdict = Verdict(
                criterion_id=vr.criterion_id,
                bidder_id=vr.bidder_id,
                verdict=vr.verdict,
                confidence=vr.confidence,
                reasoning=vr.reasoning,
                evidence_quote=vr.reasoning[:100] if vr.reasoning else None,
                source_document=vr.source_document or "unknown",
                source_page=vr.source_page or 1,
                hash=vr.verdict_hash if hasattr(vr, 'verdict_hash') and vr.verdict_hash else None
            )
            verdicts.append(verdict)
        
        # Build report
        report = build_report(tender_id, bidder_id, verdicts)
        
        # Export to PDF
        output_dir = settings.data_dir / "outputs" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = output_dir / f"{tender_id}_{bidder_id}_report.pdf"
        export_pdf(report, str(pdf_path))
        
        return FileResponse(str(pdf_path), filename=pdf_path.name)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/{tender_id}")
async def get_audit_log(tender_id: str):
    """
    Get audit log for a tender.
    
    Returns:
        Audit entries and chain verification status
    """
    try:
        db = get_db()
        
        # Get audit entries
        audit_entries = db.query(AuditLog).filter(
            AuditLog.tender_id == tender_id
        ).order_by(AuditLog.timestamp.desc()).all()
        
        if not audit_entries:
            raise HTTPException(status_code=404, detail="No audit entries found for tender")
        
        # Verify hash chain
        audit_logger = get_audit_logger()
        chain_valid = audit_logger.verify_chain(tender_id)
        
        return {
            "tender_id": tender_id,
            "chain_valid": chain_valid,
            "entries_count": len(audit_entries),
            "entries": [
                {
                    "id": entry.id,
                    "bidder_id": entry.bidder_id,
                    "criterion_id": entry.criterion_id,
                    "verdict": entry.verdict,
                    "confidence": entry.confidence,
                    "hash": entry.hash[:16] + "...",
                    "previous_hash": entry.previous_hash[:16] + "...",
                    "timestamp": entry.timestamp.isoformat(),
                    "evaluator": entry.evaluator
                }
                for entry in audit_entries
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))
