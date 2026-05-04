from backend.extraction.criterion_extractor import parse_criteria_blocks
from backend.matching.llm_judge import parse_verdict_block

# Test 1: Parse criterion blocks
print("TEST 1: Criterion Block Parsing")
criterion_text = """
### CRITERION ###
ID: C001
TEXT: Company must have minimum 5 years of experience
TYPE: technical
MANDATORY: true
THRESHOLD: 5
OPERATOR: >=
UNIT: years
EVIDENCE: experience_certificate, client_references

### CRITERION ###
ID: C002
TEXT: Annual turnover should be at least 50 crore
TYPE: financial
MANDATORY: false
THRESHOLD: 50
OPERATOR: >=
UNIT: crore
EVIDENCE: financial_statements, auditor_report
"""

criteria = parse_criteria_blocks(criterion_text, "Experience & Financial")
print(f"✓ Parsed {len(criteria)} criteria")
for c in criteria:
    print(f"  - {c.criterion_id}: {c.text[:50]}... (mandatory={c.mandatory})")

# Test 2: Parse verdict block
print("\nTEST 2: Verdict Block Parsing")
verdict_text = """
VERDICT: PASS
CONFIDENCE: 0.95
REASONING: Bidder provided clear documentation showing 8 years of experience with similar projects
EVIDENCE_QUOTE: "Our company has been delivering similar solutions for 8 years with 50+ satisfied clients"
SOURCE_DOCUMENT: experience_certificate.pdf
SOURCE_PAGE: 1
AMBIGUITY_REASON: None
"""

verdict_data = parse_verdict_block(verdict_text)
print(f"✓ Parsed verdict:")
print(f"  - Verdict: {verdict_data.get('verdict')}")
print(f"  - Confidence: {verdict_data.get('confidence')}")
print(f"  - Reasoning: {verdict_data.get('reasoning')[:60]}...")

# Test 3: Messy formatting (real LLM output)
print("\nTEST 3: Messy LLM Output (Extra whitespace, missing sections)")
messy_verdict = """

VERDICT: MANUAL_REVIEW

CONFIDENCE: 0.65

REASONING: Document provided but some details unclear - need clarification on actual project scope vs company capability claims

EVIDENCE_QUOTE: "Handled projects of similar scale"

SOURCE_DOCUMENT: portfolio.pdf
"""

verdict_data2 = parse_verdict_block(messy_verdict)
print(f"✓ Parsed messy verdict:")
print(f"  - Verdict: {verdict_data2.get('verdict')}")
print(f"  - Confidence: {verdict_data2.get('confidence')}")

print("\n✅ All delimiter-based parsing tests passed!")
print("   JSON is dead - long live delimiters! 🎉")
