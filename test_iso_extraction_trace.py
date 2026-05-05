#!/usr/bin/env python3
"""
Debug test: Trace through entire extraction pipeline for ISO criterion.
"""
import sys
sys.path.insert(0, "/content")

from backend.extraction.ner_extractor import extract_entities
from backend.verdict.generator import _extract_value
from backend.extraction.schemas import Criterion

iso_text = """ISO 9001:2015 CERTIFICATE

Certificate Number: QMS-2020-12345
Organization: Test Bidder Inc
Valid From: 15/06/2020
Valid Till: 15/06/2027

This certificate confirms that the organization has been certified against 
the ISO 9001:2015 standard for Quality Management Systems.
"""

print("=" * 70)
print("DOCUMENT TEXT:")
print(iso_text)
print("=" * 70)

# Step 1: Extract entities
print("\nSTEP 1: Extract entities")
entities = extract_entities(iso_text)
print(f"Extracted entities: {entities}")
print(f"  ISO_CERT: {entities.get('ISO_CERT')}")
print(f"  VALID_DATE: {entities.get('VALID_DATE')}")

# Step 2: Extract value via _extract_value
print("\nSTEP 2: Extract value via _extract_value()")
criterion = Criterion(
    criterion_id="C3",
    text="ISO 9001:2015 certification should be valid",
    criterion_type="compliance",
    mandatory=True,
    threshold=None,
    operator=">=",
    unit=None,
    evidence_docs=[],
    source_section="Eligibility",
    source_text="ISO 9001:2015 certification should be valid"
)

extracted_value, normalised_value = _extract_value(criterion, iso_text)
print(f"extracted_value: '{extracted_value}'")
print(f"normalised_value: {normalised_value}")
