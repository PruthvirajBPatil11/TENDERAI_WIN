import sys
sys.path.insert(0, '.')

from backend.extraction.schemas import Criterion, BidderValue
from backend.matching.rule_engine import apply_rule, _convert_threshold_to_rupees

# Test unit conversion
print("Unit Conversion Tests:")
print(f"  5 crore = {_convert_threshold_to_rupees(5, 'crore')} rupees")
print(f"  10 lakh = {_convert_threshold_to_rupees(10, 'lakh')} rupees")
print(f"  1000 rupees = {_convert_threshold_to_rupees(1000, 'rupees')} rupees")

# Create test criterion (5 crore threshold)
criterion = Criterion(
    criterion_id="C001",
    text="Minimum turnover of Rs. 5 crore",
    criterion_type="financial",
    mandatory=True,
    threshold=5,          # 5 in crores
    unit="crore",
    operator=">=",
    evidence_docs=["financial_statement"],
    source_section="Financial Eligibility",
    source_text="Rs. 5 crore"
)

# Test Bidder B (2.1 crore - should FAIL)
print("\n" + "="*60)
print("TEST 1: Bidder B - Rs. 2.1 crore (below 5 crore threshold)")
bidder_b = BidderValue(
    criterion_id="C001",
    bidder_id="bidder_B",
    extracted_value="Rs. 2,10,00,000",
    normalised_value=21000000.0,
    source_document="balance_sheet.pdf",
    source_page=1,
    extraction_method="pdfplumber",
    ocr_confidence=0.96
)

verdict, confidence, reasoning = apply_rule(criterion, bidder_b)
print(f"Verdict: {verdict}")
print(f"Confidence: {confidence}")
print(f"Reasoning: {reasoning}")
assert verdict == "FAIL", f"Expected FAIL, got {verdict}"
print("✓ CORRECT - Bidder B should FAIL\n")

# Test Bidder A (8.2 crore - should PASS)
print("TEST 2: Bidder A - Rs. 8.2 crore (above 5 crore threshold)")
bidder_a = BidderValue(
    criterion_id="C001",
    bidder_id="bidder_A",
    extracted_value="Rs. 8,20,00,000",
    normalised_value=82000000.0,
    source_document="balance_sheet.pdf",
    source_page=1,
    extraction_method="pdfplumber",
    ocr_confidence=0.97
)

verdict, confidence, reasoning = apply_rule(criterion, bidder_a)
print(f"Verdict: {verdict}")
print(f"Confidence: {confidence}")
print(f"Reasoning: {reasoning}")
assert verdict == "PASS", f"Expected PASS, got {verdict}"
print("✓ CORRECT - Bidder A should PASS\n")

print("="*60)
print("✅ All tests passed! Unit conversion is working correctly.")
