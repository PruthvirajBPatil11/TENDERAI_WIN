"""
SQLAlchemy models for database schema.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Tender(Base):
    """Tender document record."""
    __tablename__ = "tenders"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=False)
    doc_type = Column(String)  # DIGITAL_PDF, SCANNED_PDF, IMAGE, DOCX


class Bidder(Base):
    """Bidder submission record."""
    __tablename__ = "bidders"
    
    id = Column(String, primary_key=True)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    name = Column(String, nullable=False)
    registration_number = Column(String)
    submission_date = Column(DateTime, default=datetime.utcnow)


class BidderDocument(Base):
    """Bidder document with OCR confidence scores."""
    __tablename__ = "bidder_documents"
    
    doc_id = Column(String, primary_key=True)
    bidder_id = Column(String, ForeignKey("bidders.id"), nullable=False)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    doc_type = Column(String)  # DIGITAL_PDF, SCANNED_PDF, IMAGE, DOCX
    extracted_text = Column(Text)
    ocr_confidence = Column(Float, default=0.99)  # Actual OCR confidence, not 0.5 default
    extraction_method = Column(String)  # pdfplumber, ocr, ocr_fallback, docx, unknown
    upload_date = Column(DateTime, default=datetime.utcnow)


class CriterionRecord(Base):
    """Extracted criterion record."""
    __tablename__ = "criteria"
    
    id = Column(String, primary_key=True)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    text = Column(Text, nullable=False)
    criterion_type = Column(String)  # financial, technical, compliance, document
    mandatory = Column(Boolean, default=True)
    threshold = Column(Float)
    operator = Column(String)  # >=, <=, ==, contains, >=N_in_M_years
    unit = Column(String)


class VerdictRecord(Base):
    """Evaluation verdict record."""
    __tablename__ = "verdicts"
    
    id = Column(String, primary_key=True)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    bidder_id = Column(String, ForeignKey("bidders.id"), nullable=False)
    criterion_id = Column(String, ForeignKey("criteria.id"), nullable=False)
    verdict = Column(String)  # PASS, FAIL, MANUAL_REVIEW
    confidence = Column(Float)
    reasoning = Column(Text)
    source_document = Column(String)
    source_page = Column(Integer)
    verdict_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Immutable audit trail with hash chain."""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String, nullable=False)
    bidder_id = Column(String)
    criterion_id = Column(String)
    verdict = Column(String)
    confidence = Column(Float)
    reasoning = Column(Text)
    source_doc = Column(String)
    source_page = Column(Integer)
    hash = Column(String, nullable=False)
    previous_hash = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    evaluator = Column(String, default="system")
