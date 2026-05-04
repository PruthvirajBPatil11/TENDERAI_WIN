"""
CRUD operations for database models.
"""

import logging
from sqlalchemy.orm import Session
from backend.database.models import Tender, Bidder, CriterionRecord, VerdictRecord
from backend.extraction.schemas import Criterion, Verdict

logger = logging.getLogger(__name__)


def create_tender(db: Session, tender_id: str, filename: str, file_path: str, doc_type: str) -> Tender:
    """Create a new tender record."""
    tender = Tender(id=tender_id, filename=filename, file_path=file_path, doc_type=doc_type)
    db.add(tender)
    db.commit()
    return tender


def create_bidder(db: Session, bidder_id: str, tender_id: str, name: str, registration_number: str = None) -> Bidder:
    """Create a new bidder record."""
    bidder = Bidder(id=bidder_id, tender_id=tender_id, name=name, registration_number=registration_number)
    db.add(bidder)
    db.commit()
    return bidder


def create_criterion(db: Session, criterion: Criterion, tender_id: str) -> CriterionRecord:
    """Create a new criterion record."""
    # Generate unique ID by combining tender_id and criterion_id
    unique_id = f"{tender_id}_{criterion.criterion_id}"
    
    criterion_record = CriterionRecord(
        id=unique_id,
        tender_id=tender_id,
        text=criterion.text,
        criterion_type=criterion.criterion_type,
        mandatory=criterion.mandatory,
        threshold=criterion.threshold,
        operator=criterion.operator,
        unit=criterion.unit
    )
    db.add(criterion_record)
    db.commit()
    return criterion_record


def create_verdict(db: Session, verdict: Verdict, tender_id: str) -> VerdictRecord:
    """Create a new verdict record."""
    verdict_record = VerdictRecord(
        id=f"{verdict.criterion_id}_{verdict.bidder_id}",
        tender_id=tender_id,
        bidder_id=verdict.bidder_id,
        criterion_id=verdict.criterion_id,
        verdict=verdict.verdict,
        confidence=verdict.confidence,
        reasoning=verdict.reasoning,
        source_document=verdict.source_document,
        source_page=verdict.source_page,
        verdict_hash=verdict.hash
    )
    db.add(verdict_record)
    db.commit()
    return verdict_record


def get_tender(db: Session, tender_id: str) -> Tender:
    """Get a tender by ID."""
    return db.query(Tender).filter(Tender.id == tender_id).first()


def get_bidder(db: Session, bidder_id: str) -> Bidder:
    """Get a bidder by ID."""
    return db.query(Bidder).filter(Bidder.id == bidder_id).first()


def get_criteria_for_tender(db: Session, tender_id: str) -> list[CriterionRecord]:
    """Get all criteria for a tender."""
    return db.query(CriterionRecord).filter(CriterionRecord.tender_id == tender_id).all()


def get_verdicts_for_bidder(db: Session, bidder_id: str) -> list[VerdictRecord]:
    """Get all verdicts for a bidder."""
    return db.query(VerdictRecord).filter(VerdictRecord.bidder_id == bidder_id).all()
