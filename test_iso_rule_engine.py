#!/usr/bin/env python3
"""
Debug test: Direct rule engine ISO check with actual extracted value.
"""
import sys
sys.path.insert(0, "/content")

from backend.extraction.schemas import Criterion, BidderValue
from backend.matching.rule_engine import apply_rule

# ===== TEST 1: With full extracted_value including date =====
print("=" * 70)
print("TEST 1: ISO with date 'ISO 9001:2015, valid till 15/06/2027'")
print("=" * 70)

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

bidder_value = BidderValue(
    criterion_id="C3",
    bidder_id="B001",
    extracted_value="ISO 9001:2015, valid till 15/06/2027",
    normalised_value=1.0,
    source_document="iso_certificate.pdf",
    source_page=1,
    extraction_method="ner_extractor",
    ocr_confidence=0.82
)

verdict, confidence = apply_rule(criterion, bidder_value)
print(f"Result: {verdict} (confidence={confidence})")
print()

# ===== TEST 2: Just ISO cert without date =====
print("=" * 70)
print("TEST 2: ISO without date 'ISO 9001:2015'")
print("=" * 70)

bidder_value2 = BidderValue(
    criterion_id="C3",
    bidder_id="B001",
    extracted_value="ISO 9001:2015",
    normalised_value=1.0,
    source_document="iso_certificate.pdf",
    source_page=1,
    extraction_method="ner_extractor",
    ocr_confidence=0.82
)

verdict2, confidence2 = apply_rule(criterion, bidder_value2)
print(f"Result: {verdict2} (confidence={confidence2})")
print()

# ===== TEST 3: Expired date =====
print("=" * 70)
print("TEST 3: ISO with expired date 'ISO 9001:2015, valid till 15/06/2020'")
print("=" * 70)

bidder_value3 = BidderValue(
    criterion_id="C3",
    bidder_id="B001",
    extracted_value="ISO 9001:2015, valid till 15/06/2020",
    normalised_value=1.0,
    source_document="iso_certificate.pdf",
    source_page=1,
    extraction_method="ner_extractor",
    ocr_confidence=0.82
)

verdict3, confidence3 = apply_rule(criterion, bidder_value3)
print(f"Result: {verdict3} (confidence={confidence3})")
print()

# ===== TEST 4: Both dates (should use last) =====
print("=" * 70)
print("TEST 4: ISO with both dates (should use last)")
print("=" * 70)

bidder_value4 = BidderValue(
    criterion_id="C3",
    bidder_id="B001",
    extracted_value="ISO 9001:2015 Valid From: 15/06/2020 Valid Till: 15/06/2027",
    normalised_value=1.0,
    source_document="iso_certificate.pdf",
    source_page=1,
    extraction_method="ner_extractor",
    ocr_confidence=0.82
)

verdict4, confidence4 = apply_rule(criterion, bidder_value4)
print(f"Result: {verdict4} (confidence={confidence4})")
