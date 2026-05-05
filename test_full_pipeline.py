"""
Test script to upload bidder and evaluate against criteria.
"""

import os
import requests
import json
from pathlib import Path

# Load environment
env_file = Path('.env')
if env_file.exists():
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ[k.strip()] = v.strip()

# Setup database with fresh schema
from backend.database.db import engine
from backend.database.models import Base, Tender, CriterionRecord

print("Dropping and recreating database schema...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] Database schema recreated")

# Create a test tender
from backend.database.db import SessionLocal

db = SessionLocal()

# Clear existing data
db.query(CriterionRecord).delete()
db.query(Tender).delete()
db.commit()

tender_id = "T001"
tender = Tender(
    id=tender_id,
    filename="Test Tender",
    file_path="/data/test_tender.txt",
    doc_type="DIGITAL_PDF"
)
db.add(tender)

# Add some criteria
criteria = [
    CriterionRecord(
        id="C1",
        tender_id=tender_id,
        text="Annual turnover should be at least 10 lakhs",
        criterion_type="financial",
        mandatory=True,
        threshold=10,
        operator=">=",
        unit="lakh"
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
        text="Balance sheet for FY 2023-24 should be provided",
        criterion_type="document",
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

# Now test the API
API_BASE = "http://localhost:8000"

# Test 1: Upload bidder documents
print("\n--- Testing Document Upload ---")

# Create test files
test_files_dir = Path("data/test_uploads")
test_files_dir.mkdir(parents=True, exist_ok=True)

# Create test document files
test_files = [
    ("balance_sheet_FY24.pdf", "This is a balance sheet PDF for FY 2023-24 with annual turnover of Rs. 25 lakhs"),
    ("gst_certificate.pdf", "GST Certificate Valid till 31-12-2025 for GSTIN 07AAKCU5055K1ZZ"),
    ("iso_certificate.pdf", "ISO 9001:2015 Certificate Valid till 15-06-2026"),
]

for filename, content in test_files:
    filepath = test_files_dir / filename
    filepath.write_text(content)

# Upload
bidder_name = "TestBidder Inc"
files = [
    ("files", (test_files[0][0], open(test_files_dir / test_files[0][0], "rb"))),
    ("files", (test_files[1][0], open(test_files_dir / test_files[1][0], "rb"))),
    ("files", (test_files[2][0], open(test_files_dir / test_files[2][0], "rb"))),
]

response = requests.post(
    f"{API_BASE}/bidder/upload",
    data={"tender_id": tender_id, "bidder_name": bidder_name},
    files=files
)

print(f"Upload response status: {response.status_code}")
if response.status_code == 200:
    upload_result = response.json()
    print(f"[OK] Upload successful")
    print(f"  Bidder ID: {upload_result['bidder_id']}")
    print(f"  Files processed: {upload_result['files_count']}")
    
    for file_info in upload_result['files']:
        if 'ocr_confidence' in file_info:
            print(f"    {file_info['filename']}: confidence={file_info.get('ocr_confidence', 'N/A')}, type={file_info['doc_type']}")
    
    bidder_id = upload_result['bidder_id']
else:
    print(f"[FAIL] Upload failed: {response.text}")
    exit(1)

# Close files
for _, (_, f) in files:
    f.close()

# Test 2: Evaluate
print("\n--- Testing Evaluation ---")

response = requests.post(
    f"{API_BASE}/evaluate/",
    json={"tender_id": tender_id, "bidder_id": bidder_id}
)

print(f"Evaluation response status: {response.status_code}")
if response.status_code == 200:
    eval_result = response.json()
    print(f"[OK] Evaluation successful")
    print(f"  Verdicts: {eval_result['verdicts_count']}")
    
    for verdict in eval_result['verdicts']:
        print(f"    {verdict['criterion_id']}: {verdict['verdict']} (confidence={verdict['confidence']:.2f})")
        if 'reasoning' in verdict:
            print(f"      Reasoning: {verdict['reasoning'][:80]}")
else:
    print(f"[FAIL] Evaluation failed: {response.text}")

db.close()
print("\n[OK] Test complete")
