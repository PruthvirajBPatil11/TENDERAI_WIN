"""
Direct integration test - creates bidder documents in DB and tests evaluation.
Bypasses OCR/upload to focus on evaluation logic.
"""

import os
import sys
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

print("="*70)
print("INTEGRATION TEST - Evaluation Pipeline (No OCR)")
print("="*70)

# Step 1: Setup database
print("\n[STEP 1] Setting up database...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] Database recreated")

db = SessionLocal()

# Step 2: Create tender
print("\n[STEP 2] Creating tender and criteria...")
tender_id = "T001"
tender = Tender(
    id=tender_id,
    filename="Test Tender",
    file_path="/data/test_tender.txt",
    doc_type="DIGITAL_PDF"
)
db.add(tender)

# Create criteria
criteria = [
    CriterionRecord(
        id="C1",
        tender_id=tender_id,
        text="Annual turnover should be at least 5 crore",
        criterion_type="financial",
        mandatory=True,
        threshold=50000000.0,
        operator=">=",
        unit="INR"
    ),
    CriterionRecord(
        id="C2",
        tender_id=tender_id,
        text="GST Certificate must be valid",
        criterion_type="compliance",
        mandatory=True,
        threshold=None,
        operator=None,
        unit=None
    ),
    CriterionRecord(
        id="C3",
        tender_id=tender_id,
        text="ISO 9001:2015 certification should be valid",
        criterion_type="technical",
        mandatory=True,
        threshold=None,
        operator=None,
        unit=None
    ),
]

for crit in criteria:
    db.add(crit)

db.commit()
print(f"[OK] Created tender {tender_id} with {len(criteria)} criteria")

# Step 3: Create bidder
print("\n[STEP 3] Creating bidder...")
bidder_id = "BIDDER001"
bidder = Bidder(
    id=bidder_id,
    tender_id=tender_id,
    name="Test Bidder Inc"
)
db.add(bidder)

# Step 4: Create bidder documents (bypassing OCR)
print("\n[STEP 4] Creating bidder documents with pre-extracted text...")

# Financial document with turnover
financial_doc = BidderDocument(
    doc_id="doc_financial_001",
    bidder_id=bidder_id,
    tender_id=tender_id,
    filename="balance_sheet_FY24.pdf",
    file_path="/data/uploads/balance_sheet_FY24.pdf",
    doc_type="DIGITAL_PDF",
    extracted_text="""
    BALANCE SHEET FY 2024-25
    
    Annual Turnover: Rs. 8.2 crore
    Net Profit: Rs. 1.5 crore
    Total Assets: Rs. 12 crore
    
    This certifies that the company has maintained a turnover of Rs. 8,20,00,000 
    for the financial year 2024-25.
    """,
    ocr_confidence=0.99,  # Digital PDF has high confidence
    extraction_method="pdfplumber"
)
db.add(financial_doc)

# GST document
gst_doc = BidderDocument(
    doc_id="doc_gst_001",
    bidder_id=bidder_id,
    tender_id=tender_id,
    filename="gst_certificate.pdf",
    file_path="/data/uploads/gst_certificate.pdf",
    doc_type="SCANNED_PDF",
    extracted_text="""
    GST CERTIFICATE
    
    GSTIN: 07AAKCU5055K1ZZ
    Business Name: Test Bidder Inc
    Registration Date: 01/04/2018
    Status: Active
    
    This certificate confirms that the above entity is registered under GST.
    """,
    ocr_confidence=0.82,  # Scanned PDF has medium confidence
    extraction_method="ocr"
)
db.add(gst_doc)

# ISO document
iso_doc = BidderDocument(
    doc_id="doc_iso_001",
    bidder_id=bidder_id,
    tender_id=tender_id,
    filename="iso_certificate.pdf",
    file_path="/data/uploads/iso_certificate.pdf",
    doc_type="SCANNED_PDF",
    extracted_text="""
    ISO 9001:2015 CERTIFICATE
    
    Certificate Number: QMS-2020-12345
    Organization: Test Bidder Inc
    Valid From: 15/06/2020
    Valid Till: 15/06/2027
    
    This certificate confirms that the organization has been certified against 
    the ISO 9001:2015 standard for Quality Management Systems.
    """,
    ocr_confidence=0.82,
    extraction_method="ocr"
)
db.add(iso_doc)

db.commit()
print(f"[OK] Created {3} bidder documents")
print(f"     - balance_sheet_FY24.pdf (confidence=0.99)")
print(f"     - gst_certificate.pdf (confidence=0.82)")
print(f"     - iso_certificate.pdf (confidence=0.82)")

# Step 5: Load documents for evaluation
print("\n[STEP 5] Loading documents for evaluation...")
doc_records = db.query(BidderDocument).filter(
    BidderDocument.bidder_id == bidder_id
).all()

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

print(f"[OK] Loaded {len(bidder_docs)} documents")
for d in bidder_docs:
    print(f"     - {d['filename']}: ocr_confidence={d['ocr_confidence']:.3f}, "
          f"text_len={len(d['text'])}")

# Step 6: Evaluate each criterion
print("\n[STEP 6] Evaluating criteria...")
print("-" * 70)

criterion_records = db.query(CriterionRecord).filter(
    CriterionRecord.tender_id == tender_id
).all()

verdicts = []
for crit_record in criterion_records:
    criterion = Criterion(
        criterion_id=crit_record.id,
        text=crit_record.text,
        criterion_type=crit_record.criterion_type or "technical",
        mandatory=crit_record.mandatory or True,
        threshold=crit_record.threshold,
        operator=crit_record.operator,
        unit=crit_record.unit,
        evidence_docs=[],
        source_section="Tender",
        source_text=crit_record.text
    )
    
    print(f"\nEvaluating {crit_record.id}: {crit_record.text[:50]}...")
    
    verdict = generate_verdict(criterion, bidder_docs, bidder_id)
    verdicts.append(verdict)
    
    print(f"  Verdict: {verdict.verdict}")
    print(f"  Confidence: {verdict.confidence:.2f}")
    print(f"  OCR Confidence: {verdict.ocr_confidence:.3f}")
    print(f"  Source: {verdict.source_document}")
    print(f"  Reasoning: {verdict.reasoning[:100]}...")

# Step 7: Summary
print("\n" + "="*70)
print("EVALUATION RESULTS")
print("="*70)

for i, v in enumerate(verdicts, 1):
    print(f"\nC{i}: {v.verdict}")
    print(f"    Confidence: {v.confidence:.2f}")
    print(f"    OCR Confidence: {v.ocr_confidence:.3f}")
    print(f"    Source Document: {v.source_document}")

# Check for success
mandatory_verdicts = verdicts[:3]  # C1, C2, C3 are mandatory
all_pass = all(v.verdict == "PASS" for v in mandatory_verdicts)

if all_pass:
    print("\n[SUCCESS] All mandatory criteria PASSED!")
    print("Expected outcome: ELIGIBLE")
else:
    print("\n[INFO] Not all criteria passed - reviewing details:")
    for i, v in enumerate(mandatory_verdicts, 1):
        if v.verdict != "PASS":
            print(f"  C{i}: {v.verdict} - {v.reasoning[:80]}")

db.close()
print("\n" + "="*70)
