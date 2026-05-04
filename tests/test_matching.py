"""
Tests for matching and verdict generation.
"""

import pytest
from backend.matching.rule_engine import apply_rule
from backend.extraction.schemas import Criterion, BidderValue
from backend.matching.confidence_scorer import final_verdict


def test_rule_engine_turnover_pass():
    """Test rule engine for passing turnover criterion."""
    
    criterion = Criterion(
        criterion_id="C001",
        text="Minimum annual turnover of ₹5 crore",
        criterion_type="financial",
        mandatory=True,
        threshold=50000000.0,
        operator=">=",
        unit="INR",
        evidence_docs=[],
        source_section="Eligibility",
        source_text="Minimum annual turnover of ₹5 crore"
    )
    
    bidder_value = BidderValue(
        criterion_id="C001",
        bidder_id="B001",
        extracted_value="₹8.2 crore",
        normalised_value=82000000.0,
        source_document="turnover.pdf",
        source_page=1,
        extraction_method="ocr",
        ocr_confidence=0.95
    )
    
    verdict, confidence, reasoning = apply_rule(criterion, bidder_value)
    
    assert verdict == "PASS"
    assert confidence > 0.9
    assert "meets minimum" in reasoning.lower()


def test_rule_engine_turnover_fail():
    """Test rule engine for failing turnover criterion."""
    
    criterion = Criterion(
        criterion_id="C001",
        text="Minimum annual turnover of ₹5 crore",
        criterion_type="financial",
        mandatory=True,
        threshold=50000000.0,
        operator=">=",
        unit="INR",
        evidence_docs=[],
        source_section="Eligibility",
        source_text="Minimum annual turnover of ₹5 crore"
    )
    
    bidder_value = BidderValue(
        criterion_id="C001",
        bidder_id="B002",
        extracted_value="₹2.1 crore",
        normalised_value=21000000.0,
        source_document="turnover.pdf",
        source_page=1,
        extraction_method="ocr",
        ocr_confidence=0.95
    )
    
    verdict, confidence, reasoning = apply_rule(criterion, bidder_value)
    
    assert verdict == "FAIL"
    assert confidence > 0.7
    assert "below" in reasoning.lower()


def test_final_verdict_low_ocr_confidence():
    """Test that low OCR confidence overrides to MANUAL_REVIEW."""
    
    criterion = Criterion(
        criterion_id="C001",
        text="Test criterion",
        criterion_type="financial",
        mandatory=True,
        threshold=5000000.0,
        operator=">=",
        unit="INR",
        evidence_docs=[],
        source_section="Test",
        source_text="Test"
    )
    
    bidder_value = BidderValue(
        criterion_id="C001",
        bidder_id="B001",
        extracted_value="₹8 crore",
        normalised_value=80000000.0,
        source_document="test.pdf",
        source_page=1,
        extraction_method="ocr",
        ocr_confidence=0.7  # Below threshold of 0.80
    )
    
    rule_result = ("PASS", 0.99, "Value passes")
    semantic_result = ("PASS", 0.9, "test")
    
    verdict = final_verdict(rule_result, semantic_result, None, 0.7, criterion, bidder_value)
    
    assert verdict.verdict == "MANUAL_REVIEW"
    assert "OCR confidence" in verdict.reasoning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
