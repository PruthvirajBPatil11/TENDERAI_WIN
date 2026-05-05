"""Debug ISO certificate extraction"""

from backend.extraction.ner_extractor import extract_entities
from backend.extraction.value_normaliser import is_date_valid

iso_text = """
ISO 9001:2015 CERTIFICATE

Certificate Number: QMS-2020-12345
Organization: Test Bidder Inc
Valid From: 15/06/2020
Valid Till: 15/06/2027

This certificate confirms that the organization has been certified against 
the ISO 9001:2015 standard for Quality Management Systems.
"""

print("ISO Certificate Text:")
print(iso_text)
print("\n" + "="*70)

entities = extract_entities(iso_text)
print("\nExtracted Entities:")
print(f"  ISO_CERT: {entities.get('ISO_CERT')}")
print(f"  VALID_DATE: {entities.get('VALID_DATE')}")

print("\n" + "="*70)
print("Testing Date Validation:")
dates = entities.get('VALID_DATE', [])
for date_str in dates:
    valid = is_date_valid(date_str)
    print(f"  {date_str}: valid={valid}")

print("\n" + "="*70)
print("Testing Rule Engine Logic:")

from backend.extraction.schemas import Criterion, BidderValue
from backend.matching.rule_engine import apply_rule

criterion = Criterion(
    criterion_id="C3",
    text="ISO 9001:2015 certification should be valid",
    criterion_type="technical",
    mandatory=True,
    threshold=None,
    operator=None,
    unit=None,
    evidence_docs=[],
    source_section="Tender",
    source_text="ISO 9001:2015 certification should be valid"
)

# Test with extracted values
iso_cert = entities.get('ISO_CERT', [''])[0]
valid_date = entities.get('VALID_DATE', [''])[0]
extracted_value = f"{iso_cert}, valid till {valid_date}"

print(f"\nCreating BidderValue with:")
print(f"  extracted_value: '{extracted_value}'")

bidder_value = BidderValue(
    criterion_id="C3",
    bidder_id="B001",
    extracted_value=extracted_value,
    normalised_value=1.0,
    source_document="iso_certificate.pdf",
    source_page=1,
    extraction_method="ocr",
    ocr_confidence=0.82
)

verdict_str, confidence = apply_rule(criterion, bidder_value)
print(f"\nRule Engine Result:")
print(f"  Verdict: {verdict_str}")
print(f"  Confidence: {confidence}")
