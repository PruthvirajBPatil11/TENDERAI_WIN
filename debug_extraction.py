#!/usr/bin/env python3
"""
Debug script to trace the criteria extraction pipeline step by step.
"""

import sys
from pathlib import Path

# Add project root
project_root = Path("d:/TENDER-EVAL-AI")
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

from backend.ingestion.detector import detect_doc_type
from backend.ingestion.pdf_extractor import extract_digital_pdf
from backend.ingestion.chunker import chunk_document
from backend.extraction.section_classifier import classify_sections
from backend.extraction.criterion_extractor import extract_criteria

# Load mock tender
tender_file = Path("d:/TENDER-EVAL-AI/data/mock/tender_crpf_construction.txt")

print("\n" + "=" * 80)
print("STEP 1: LOAD TENDER TEXT")
print("=" * 80)

with open(tender_file, "r") as f:
    tender_text = f.read()

print(f"Tender loaded: {len(tender_text)} characters")
print(f"First 500 chars:\n{tender_text[:500]}")

print("\n" + "=" * 80)
print("STEP 2: SIMULATE PDF EXTRACTION (pages)")
print("=" * 80)

# Simulate PDF pages (for TXT files, treat as single page)
pages = [{"text": tender_text, "page_no": 1}]
print(f"Simulated {len(pages)} page(s)")

print("\n" + "=" * 80)
print("STEP 3: CHUNK DOCUMENT INTO SECTIONS")
print("=" * 80)

sections = chunk_document(pages)
print(f"\n[OK] Chunked into {len(sections)} sections:\n")

for i, section in enumerate(sections, 1):
    print(f"\nSection {i}: {section['section_name']}")
    print(f"  Text length: {len(section['text'])} characters")
    print(f"  First 200 chars: {section['text'][:200]}")
    print(f"  Pages: {section['page_nos']}")

print("\n" + "=" * 80)
print("STEP 4: CLASSIFY SECTIONS (identify eligibility sections)")
print("=" * 80)

classified = classify_sections(sections)

for i, section in enumerate(classified, 1):
    is_elig = section.get("is_eligibility_section", False)
    status = "[OK] ELIGIBILITY" if is_elig else "[NO] OTHER"
    print(f"\n{status} - {section['section_name']}")

eligibility_sections = [s for s in classified if s.get("is_eligibility_section", False)]
print(f"\n[OK] Found {len(eligibility_sections)} eligibility sections")

if not eligibility_sections:
    print("\n[ERROR] PROBLEM: No eligibility sections found!")
    print("This is why criteria extraction returns empty.")
    sys.exit(1)

print("\n" + "=" * 80)
print("STEP 5: EXTRACT CRITERIA FROM ELIGIBILITY SECTIONS")
print("=" * 80)

all_criteria = []
for section in eligibility_sections:
    print(f"\n[EXTRACT] Extracting from: {section['section_name']}")
    print(f"   Text length: {len(section['text'])} characters")
    
    criteria = extract_criteria(section["text"], section["section_name"])
    print(f"   [OK] Extracted {len(criteria)} criteria")
    
    for i, c in enumerate(criteria, 1):
        print(f"     {i}. [{c.criterion_type}] {c.text[:80]}...")
    
    all_criteria.extend(criteria)

print(f"\n" + "=" * 80)
print(f"SUMMARY: Extracted {len(all_criteria)} total criteria")
print("=" * 80)

if len(all_criteria) > 0:
    print("\n[OK] SUCCESS - Criteria were extracted!")
    for c in all_criteria:
        print(f"  - [{c.criterion_id}] {c.text}")
else:
    print("\n[ERROR] FAILURE - No criteria extracted")
