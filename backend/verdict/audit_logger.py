"""
Audit logger - maintains immutable hash chain of verdicts.
"""

import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from backend.database.db import get_db

logger = logging.getLogger(__name__)


class AuditLogger:
    """Maintains an immutable audit trail with SHA-256 hash chain."""
    
    def __init__(self):
        """Initialize the audit logger."""
        self.db = get_db()
    
    def log(self, verdict, tender_id: str, bidder_id: str = None, evaluator: str = "system"):
        """
        Log a verdict to the audit trail with hash chain.
        
        Args:
            verdict: Verdict object to log
            tender_id: ID of the tender
            bidder_id: ID of the bidder (optional, extracted from verdict)
            evaluator: Name/ID of the evaluator
        """
        bidder_id = bidder_id or verdict.bidder_id
        
        try:
            # Get the previous hash for this tender
            from backend.database.models import AuditLog
            from sqlalchemy.orm import Session
            
            db: Session = self.db
            
            last_entry = db.query(AuditLog).filter(
                AuditLog.tender_id == tender_id
            ).order_by(AuditLog.id.desc()).first()
            
            previous_hash = last_entry.hash if last_entry else "GENESIS"
            
            # Create audit log entry
            audit_entry = AuditLog(
                tender_id=tender_id,
                bidder_id=bidder_id,
                criterion_id=verdict.criterion_id,
                verdict=verdict.verdict,
                confidence=verdict.confidence,
                reasoning=verdict.reasoning,
                source_doc=verdict.source_document,
                source_page=verdict.source_page,
                hash=verdict.hash,
                previous_hash=previous_hash,
                timestamp=datetime.utcnow(),
                evaluator=evaluator
            )
            
            db.add(audit_entry)
            db.commit()
            
            logger.info(f"Audit logged: {bidder_id} criterion {verdict.criterion_id} = {verdict.verdict}")
        
        except Exception as e:
            logger.error(f"Error logging verdict to audit trail: {e}")
            raise
    
    def verify_chain(self, tender_id: str) -> bool:
        """
        Verify the integrity of the hash chain for a tender.
        
        Args:
            tender_id: ID of the tender to verify
            
        Returns:
            True if chain is valid, False otherwise
        """
        try:
            from backend.database.models import AuditLog
            from sqlalchemy.orm import Session
            
            db: Session = self.db
            
            entries = db.query(AuditLog).filter(
                AuditLog.tender_id == tender_id
            ).order_by(AuditLog.id.asc()).all()
            
            if not entries:
                logger.warning(f"No audit entries found for tender {tender_id}")
                return True
            
            # Verify first entry's previous hash
            if entries[0].previous_hash != "GENESIS":
                logger.error(f"First entry does not have GENESIS previous hash")
                return False
            
            # Verify chain continuity
            for i in range(1, len(entries)):
                expected_prev = entries[i - 1].hash
                actual_prev = entries[i].previous_hash
                
                if expected_prev != actual_prev:
                    logger.error(f"Hash chain broken at entry {i}: expected {expected_prev}, got {actual_prev}")
                    return False
            
            logger.info(f"Hash chain verified for tender {tender_id} ({len(entries)} entries)")
            return True
        
        except Exception as e:
            logger.error(f"Error verifying hash chain: {e}")
            return False


# Global instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get or create the audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
