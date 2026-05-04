"""
Rule-based deterministic matching engine for numeric and document criteria.
"""

import logging
from backend.extraction.schemas import Criterion, BidderValue, Verdict
from backend.extraction.value_normaliser import is_date_valid
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


def _convert_threshold_to_rupees(threshold: float, unit: str) -> float:
    """Convert threshold to rupees based on unit."""
    if threshold is None:
        return None
    
    unit = (unit or "").lower()
    
    # Unit conversion factors to rupees
    conversions = {
        "crore": 10000000,      # 1 crore = 10,000,000 rupees
        "lakh": 100000,          # 1 lakh = 100,000 rupees
        "rupees": 1,
        "number": 1,
        "years": 1,              # years stay as-is
        None: 1,
        "": 1
    }
    
    factor = conversions.get(unit, 1)
    return threshold * factor


def apply_rule(criterion: Criterion, bidder_value: BidderValue) -> tuple[str, float, str]:
    """
    Apply deterministic rule matching for a criterion against bidder value.
    
    Returns:
        Tuple of (verdict_str, confidence, reasoning)
        verdict_str is one of: "PASS", "FAIL", "MANUAL_REVIEW"
    """
    reasoning = ""
    
    # If no value was extracted, manual review required
    if bidder_value.normalised_value is None and criterion.criterion_type in ["financial", "technical"]:
        return ("MANUAL_REVIEW", 0.0, f"Value could not be extracted from {bidder_value.source_document}")
    
    # Financial criteria: numeric comparison
    if criterion.criterion_type == "financial" and criterion.threshold is not None:
        if bidder_value.normalised_value is None:
            return ("MANUAL_REVIEW", 0.0, "Numeric value could not be extracted for financial criterion")
        
        # Convert threshold to same units as normalised_value (rupees)
        threshold_rupees = _convert_threshold_to_rupees(criterion.threshold, criterion.unit)
        
        # Determine OCR confidence for verdict confidence
        ocr_confidence = bidder_value.ocr_confidence or 0.5
        verdict_confidence = 0.99 if ocr_confidence > 0.85 else 0.75
        
        # Apply operator
        operator = criterion.operator or ">="
        
        if operator == ">=":
            if bidder_value.normalised_value >= threshold_rupees:
                reasoning = f"Bidder value {bidder_value.normalised_value} rupees meets minimum threshold {threshold_rupees} rupees ({criterion.threshold} {criterion.unit})"
                return ("PASS", verdict_confidence, reasoning)
            else:
                reasoning = f"Bidder value {bidder_value.normalised_value} rupees below minimum threshold {threshold_rupees} rupees ({criterion.threshold} {criterion.unit})"
                return ("FAIL", verdict_confidence, reasoning)
        
        elif operator == "<=":
            if bidder_value.normalised_value <= threshold_rupees:
                reasoning = f"Bidder value {bidder_value.normalised_value} rupees within maximum threshold {threshold_rupees} rupees ({criterion.threshold} {criterion.unit})"
                return ("PASS", verdict_confidence, reasoning)
            else:
                reasoning = f"Bidder value {bidder_value.normalised_value} rupees exceeds maximum threshold {threshold_rupees} rupees ({criterion.threshold} {criterion.unit})"
                return ("FAIL", verdict_confidence, reasoning)
        
        elif operator == "==":
            if bidder_value.normalised_value == threshold_rupees:
                reasoning = f"Bidder value {bidder_value.normalised_value} rupees matches required value {threshold_rupees} rupees ({criterion.threshold} {criterion.unit})"
                return ("PASS", verdict_confidence, reasoning)
            else:
                reasoning = f"Bidder value {bidder_value.normalised_value} rupees does not match required value {threshold_rupees} rupees ({criterion.threshold} {criterion.unit})"
                return ("FAIL", verdict_confidence, reasoning)
    
    # Date validity criteria
    if criterion.criterion_type == "compliance" and "date" in criterion.text.lower():
        if bidder_value.extracted_value:
            if is_date_valid(bidder_value.extracted_value):
                reasoning = f"Certificate dated {bidder_value.extracted_value} is currently valid"
                return ("PASS", 0.9, reasoning)
            else:
                reasoning = f"Certificate dated {bidder_value.extracted_value} has expired or is not yet valid"
                return ("FAIL", 0.9, reasoning)
    
    # Document criteria: check if document type is present
    if criterion.criterion_type == "document":
        if bidder_value.extracted_value and bidder_value.extracted_value.lower() != "not found":
            reasoning = f"Required document type '{criterion.text}' was provided"
            return ("PASS", 0.95, reasoning)
        else:
            reasoning = f"Required document type '{criterion.text}' was not provided"
            return ("FAIL", 0.95, reasoning)
    
    # Default: cannot apply rule
    return ("MANUAL_REVIEW", 0.0, f"No applicable rule for {criterion.criterion_type} criterion")
