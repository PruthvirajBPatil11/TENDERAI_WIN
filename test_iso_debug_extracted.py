#!/usr/bin/env python3
"""
Debug test: Add detailed logging to see exact extracted_value in test_evaluation.
"""
import sys
import os
sys.path.insert(0, "/content")

# Enable debug logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

from pathlib import Path

# Setup environment
env_file = Path('.env')
if env_file.exists():
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ[k.strip()] = v.strip()

from backend.database.db import SessionLocal, engine
from backend.database.models import Base, Tender, Bidder, BidderDocument, CriterionRecord, VerdictRecord
from backend.extraction.schemas import Criterion
from backend.verdict.generator import generate_verdict

print("=" * 70)
print("DEBUG TEST - Trace exact extracted_value for ISO")
print("=" * 70)

# Setup database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create tender
tender_id = "T001"
tender = Tender(
    id=tender_id,
    filename="Test Tender",
    file_path="/data/test_tender.txt",
    doc_type="DIGITAL_PDF"
)
db.add(tender)

# Create criterion
criterion_db = CriterionRecord(
    id="C3",
    tender_id=tender_id,
    text="ISO 9001:2015 certification should be valid",
    criterion_type="technical",
    mandatory=True,
    threshold=None,
    operator=None,
    unit=None
)
db.add(criterion_db)

# Create bidder
bidder_id = "B001"
bidder = Bidder(id=bidder_id, tender_id=tender_id, name="Test Bidder")
db.add(bidder)

# Create document with ISO certificate text
iso_text = """ISO 9001:2015 CERTIFICATE

Certificate Number: QMS-2020-12345
Organization: Test Bidder Inc
Valid From: 15/06/2020
Valid Till: 15/06/2027

This certificate confirms that the organization has been certified against 
the ISO 9001:2015 standard for Quality Management Systems.
"""

doc = BidderDocument(
    doc_id="DOC_ISO",
    bidder_id=bidder_id,
    tender_id=tender_id,
    filename="iso_certificate.pdf",
    file_path="/data/uploads/iso_certificate.pdf",
    doc_type="DIGITAL_PDF",
    extraction_method="manual",
    extracted_text=iso_text,
    ocr_confidence=0.82
)
db.add(doc)

db.commit()

# Now test evaluation
print("\nLoading data from DB...")
criterion_record = db.query(CriterionRecord).filter_by(id="C3").first()
bidder_docs = db.query(BidderDocument).filter_by(bidder_id=bidder_id).all()

print(f"Criterion: {criterion_record.text} (type={criterion_record.criterion_type})")
print(f"Documents: {len(bidder_docs)}")

# Convert to schema
criterion = Criterion(
    criterion_id=criterion_record.id,
    text=criterion_record.text,
    criterion_type=criterion_record.criterion_type,
    mandatory=criterion_record.mandatory,
    threshold=criterion_record.threshold,
    operator=criterion_record.operator,
    unit=criterion_record.unit,
    evidence_docs=[],
    source_section="Eligibility",
    source_text=criterion_record.text
)

# Call generate_verdict with debug
print("\nGenerating verdict...")
verdict = generate_verdict(criterion, [
    {
        "filename": doc.filename,
        "text": doc.extracted_text,
        "ocr_confidence": doc.ocr_confidence,
        "doc_type": doc.doc_type,
        "extraction_method": doc.extraction_method
    }
    for doc in bidder_docs
], bidder_id)

print(f"\nResult:")
print(f"  Verdict: {verdict.verdict}")
print(f"  Confidence: {verdict.confidence}")
print(f"  Reasoning: {verdict.reasoning}")
