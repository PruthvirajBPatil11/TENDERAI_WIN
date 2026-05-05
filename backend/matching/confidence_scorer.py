"""
Final confidence scoring and verdict determination combining all evidence.
"""

import logging
import hashlib
import json
from datetime import datetime
from backend.extraction.schemas import Criterion, BidderValue, Verdict

logger = logging.getLogger(__name__)


def final_verdict(
    rule_result: tuple,
    ocr_confidence: float,
    criterion: Criterion,
    bidder_value: BidderValue
) -> Verdict:
    """
    Combine rule engine result with OCR confidence to produce final verdict.
    
    Args:
        rule_result: Tuple of (verdict_str, confidence) from rule_engine
        ocr_confidence: OCR confidence score for the document (0.0-1.0)
        criterion: The criterion being evaluated
        bidder_value: The bidder value being evaluated
        
    Returns:
        Final Verdict object
    """
    rule_verdict, rule_confidence = rule_result
    
    final_verdict_str = rule_verdict
    final_confidence = rule_confidence
    final_reasoning = ""
    evidence_quote = bidder_value.extracted_value or ""
    
    # ===== DECISION LOGIC =====
    
    # 1. If OCR confidence is too low (< 0.80) and criterion is mandatory:
    #    Override to MANUAL_REVIEW
    if ocr_confidence < 0.80 and criterion.mandatory:
        final_verdict_str = "MANUAL_REVIEW"
        final_confidence = 0.0
        final_reasoning = f"OCR confidence {ocr_confidence:.2f} below threshold 0.80. Manual verification required."
        logger.info(f"C{criterion.criterion_id}: OCR confidence {ocr_confidence:.2f} < 0.80, forcing MANUAL_REVIEW")
    
    # 2. If rule result is already PASS or FAIL with good confidence, use it
    elif rule_verdict in ["PASS", "FAIL"] and rule_confidence >= 0.85:
        final_verdict_str = rule_verdict
        final_confidence = rule_confidence
        if rule_verdict == "PASS":
            final_reasoning = f"Criterion met with {rule_confidence:.0%} confidence"
        else:
            final_reasoning = f"Criterion not met with {rule_confidence:.0%} confidence"
        logger.info(f"C{criterion.criterion_id}: Using rule result {rule_verdict} with confidence {rule_confidence:.2f}")
    
    # 3. If rule result is MANUAL_REVIEW, keep it
    elif rule_verdict == "MANUAL_REVIEW":
        final_verdict_str = "MANUAL_REVIEW"
        final_confidence = 0.0
        final_reasoning = "Could not determine verdict from available evidence. Manual review required."
        logger.info(f"C{criterion.criterion_id}: Rule engine returned MANUAL_REVIEW")
    
    # Create hash for audit trail
    verdict_dict = {
        "criterion_id": criterion.criterion_id,
        "bidder_id": bidder_value.bidder_id,
        "verdict": final_verdict_str,
        "timestamp": datetime.utcnow().isoformat()
    }
    verdict_hash = hashlib.sha256(json.dumps(verdict_dict, sort_keys=True).encode()).hexdigest()
    
    return Verdict(
        criterion_id=criterion.criterion_id,
        bidder_id=bidder_value.bidder_id,
        verdict=final_verdict_str,
        confidence=final_confidence,
        reasoning=final_reasoning,
        evidence_quote=evidence_quote,
        source_document=bidder_value.source_document,
        source_page=bidder_value.source_page,
        hash=verdict_hash
    )
