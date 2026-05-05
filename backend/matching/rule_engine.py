"""
Rule-based deterministic matching engine for numeric and document criteria.
Implements criterion-specific evaluation logic for financial, technical, compliance, and other criteria.
"""

import logging
import re
from datetime import datetime
from backend.extraction.schemas import Criterion, BidderValue
from backend.extraction.value_normaliser import is_date_valid

logger = logging.getLogger(__name__)


def _convert_threshold_to_rupees(threshold: float, unit: str) -> float:
    """
    Convert threshold value to rupees based on unit.
    
    Args:
        threshold: Threshold value
        unit: Unit string (crore, lakh, rupees, etc.)
        
    Returns:
        Threshold value in rupees
    """
    if threshold is None:
        return None
    
    unit = (unit or "").lower()
    
    if any(u in unit for u in ['crore', 'cr']):
        return threshold * 10_000_000
    elif any(u in unit for u in ['lakh', 'lac', 'l']):
        return threshold * 100_000
    else:
        return threshold


def apply_rule(criterion: Criterion, bidder_value: BidderValue) -> tuple[str, float]:
    """
    Apply deterministic rule matching for a criterion against bidder value.
    
    Args:
        criterion: Criterion object with threshold, unit, operator, type, text
        bidder_value: Bidder value with extracted_value, normalised_value, ocr_confidence
        
    Returns:
        Tuple of (verdict_str, confidence)
        verdict_str is one of: "PASS", "FAIL", "MANUAL_REVIEW"
    """
    criterion_type = (criterion.criterion_type or "").lower()
    criterion_text = (criterion.text or "").lower()
    
    # ===== FINANCIAL CRITERIA =====
    if criterion_type == "financial":
        if bidder_value.normalised_value is None:
            logger.info(f"Financial criterion {criterion.criterion_id}: No value extracted, MANUAL_REVIEW")
            return ("MANUAL_REVIEW", 0.0)
        
        threshold_rupees = _convert_threshold_to_rupees(criterion.threshold, criterion.unit)
        operator = (criterion.operator or ">=").strip()
        
        extracted_val = bidder_value.normalised_value
        
        # Apply comparison operator
        if operator == ">=":
            passes = extracted_val >= threshold_rupees
        elif operator == "<=":
            passes = extracted_val <= threshold_rupees
        elif operator == "==":
            passes = extracted_val == threshold_rupees
        else:
            passes = extracted_val >= threshold_rupees
        
        verdict = "PASS" if passes else "FAIL"
        confidence = 0.99
        
        logger.info(f"Financial C{criterion.criterion_id}: {extracted_val} {operator} {threshold_rupees} = {verdict}")
        return (verdict, confidence)
    
    # ===== CHECK FOR ISO FIRST (before generic technical/experience) =====
    elif criterion_type in ["technical", "compliance"] and any(kw in criterion_text for kw in ['iso', '9001', 'quality', 'certification']):
        extracted = (bidder_value.extracted_value or "").upper()
        
        logger.debug(f"ISO Check for C{criterion.criterion_id}: extracted='{extracted}', criterion_text='{criterion_text}'")
        
        # Check if ISO 9001 is mentioned
        if not re.search(r'ISO\s*9001', extracted, re.IGNORECASE):
            logger.info(f"ISO criterion C{criterion.criterion_id}: ISO 9001 not found, FAIL")
            return ("FAIL", 0.85)
        
        # Look for expiry date near "expiry", "valid", "till", "upto" keywords
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        date_matches = list(re.finditer(date_pattern, extracted))
        
        logger.debug(f"ISO Check for C{criterion.criterion_id}: found {len(date_matches)} dates")
        
        if date_matches:
            # Found date, check if valid
            last_date_str = date_matches[-1].group(0)  # Use last date found
            logger.debug(f"ISO Check for C{criterion.criterion_id}: checking date {last_date_str}")
            if is_date_valid(last_date_str):
                logger.info(f"ISO criterion C{criterion.criterion_id}: Valid ISO cert with future expiry {last_date_str}, PASS")
                return ("PASS", 0.92)
            else:
                logger.info(f"ISO criterion C{criterion.criterion_id}: ISO cert expired {last_date_str}, FAIL")
                return ("FAIL", 0.95)
        else:
            # No expiry date found, assume valid but with lower confidence
            logger.info(f"ISO criterion C{criterion.criterion_id}: ISO cert found but no expiry date, PASS (low confidence)")
            return ("PASS", 0.75)
    
    # ===== TECHNICAL/EXPERIENCE CRITERIA (FOR PROJECT/CONTRACT COUNTING) =====
    elif criterion_type in ["technical", "experience"]:
        # Check if we're counting projects/contracts
        if any(kw in criterion_text for kw in ['project', 'similar', 'contract', 'work', 'experience']):
            if bidder_value.normalised_value is None:
                logger.info(f"Experience criterion {criterion.criterion_id}: No count extracted, MANUAL_REVIEW")
                return ("MANUAL_REVIEW", 0.0)
            
            count = bidder_value.normalised_value
            threshold = criterion.threshold or 0
            
            passes = count >= threshold
            verdict = "PASS" if passes else "FAIL"
            confidence = 0.85
            
            logger.info(f"Experience C{criterion.criterion_id}: count={count} >= threshold={threshold} = {verdict}")
            return (verdict, confidence)
        
        # For other technical criteria, return MANUAL_REVIEW
        return ("MANUAL_REVIEW", 0.0)
    
    # ===== COMPLIANCE CRITERIA (GST) =====
    elif criterion_type == "compliance" and any(kw in criterion_text for kw in ['gst', 'goods', 'services', 'tax']):
        extracted = (bidder_value.extracted_value or "").upper()
        
        # Check for GSTIN pattern
        gstin_pattern = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}'
        gstin_match = re.search(gstin_pattern, extracted)
        
        if not gstin_match:
            logger.info(f"GST compliance C{criterion.criterion_id}: No GSTIN found, FAIL")
            return ("FAIL", 0.95)
        
        # Check if active (not cancelled/inactive)
        if any(kw in extracted for kw in ['CANCEL', 'INACTIVE', 'SUSPENDED']):
            logger.info(f"GST compliance C{criterion.criterion_id}: GSTIN found but cancelled, FAIL")
            return ("FAIL", 0.95)
        
        # GSTIN found and not cancelled
        logger.info(f"GST compliance C{criterion.criterion_id}: Valid active GSTIN found, PASS")
        return ("PASS", 0.95)
    
    # ===== COMPLIANCE CRITERIA (OTHER) =====
    elif criterion_type == "compliance":
        # Generic compliance check: if document was found and extracted, pass
        if bidder_value.extracted_value and bidder_value.extracted_value.lower() != "not found":
            logger.info(f"Compliance C{criterion.criterion_id}: Document provided, PASS")
            return ("PASS", 0.90)
        else:
            logger.info(f"Compliance C{criterion.criterion_id}: Document not found, FAIL")
            return ("FAIL", 0.90)
    
    # ===== FALLBACK =====
    logger.info(f"No rule applicable for criterion type={criterion_type}, MANUAL_REVIEW")
    return ("MANUAL_REVIEW", 0.0)
