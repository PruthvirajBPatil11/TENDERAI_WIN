"""
Final confidence scoring and verdict determination combining all evidence.
"""

import logging
from backend.extraction.schemas import Criterion, BidderValue, Verdict
from backend.config import settings
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def final_verdict(
    rule_result: tuple,
    semantic_result: tuple,
    llm_result: Verdict | None,
    ocr_confidence: float,
    criterion: Criterion,
    bidder_value: BidderValue
) -> Verdict:
    """
    Combine rule, semantic, and LLM results to produce final verdict.
    
    Args:
        rule_result: Tuple of (verdict, confidence, reasoning) from rule_engine
        semantic_result: Tuple of (verdict, score, text) from semantic_matcher
        llm_result: Verdict object from llm_judge (may be None)
        ocr_confidence: OCR confidence score for the extracted value
        criterion: The criterion being evaluated
        bidder_value: The bidder value being evaluated
        
    Returns:
        Final Verdict object
    """
    rule_verdict, rule_conf, rule_reasoning = rule_result
    sem_verdict, sem_score, sem_text = semantic_result
    
    final_verdict_str = "MANUAL_REVIEW"
    final_confidence = 0.0
    final_reasoning = ""
    evidence_quote = ""
    
    # Decision logic:
    # 1. If OCR confidence is too low, override to MANUAL_REVIEW
    if ocr_confidence < settings.ocr_confidence_threshold:
        final_verdict_str = "MANUAL_REVIEW"
        final_confidence = 0.0
        final_reasoning = f"OCR confidence ({ocr_confidence:.2f}) below threshold ({settings.ocr_confidence_threshold}). Value verification required."
        evidence_quote = bidder_value.extracted_value
    
    # 2. If rule engine is confident (> 0.90), use rule result
    elif rule_verdict in ["PASS", "FAIL"] and rule_conf > 0.90:
        final_verdict_str = rule_verdict
        final_confidence = rule_conf
        final_reasoning = rule_reasoning
        evidence_quote = bidder_value.extracted_value
    
    # 3. If rule engine cannot decide, check semantic + LLM
    elif rule_verdict == "MANUAL_REVIEW" and (sem_verdict != "MANUAL_REVIEW" or llm_result):
        # If semantic is confident
        if sem_score > settings.semantic_similarity_pass_threshold:
            final_verdict_str = "PASS"
            final_confidence = sem_score
            final_reasoning = f"Semantic match (score: {sem_score:.2f}) with criterion. {rule_reasoning}"
            evidence_quote = sem_text[:500]
        elif sem_score < settings.semantic_similarity_review_threshold:
            final_verdict_str = "FAIL"
            final_confidence = 1.0 - sem_score
            final_reasoning = f"Semantic mismatch (score: {sem_score:.2f}) with criterion. {rule_reasoning}"
            evidence_quote = sem_text[:500]
        
        # Check LLM result if available
        if llm_result and llm_result.verdict != "MANUAL_REVIEW":
            final_verdict_str = llm_result.verdict
            final_confidence = llm_result.confidence
            final_reasoning = llm_result.reasoning
            evidence_quote = llm_result.evidence_quote
    
    # Default to LLM result if available
    elif llm_result:
        final_verdict_str = llm_result.verdict
        final_confidence = llm_result.confidence
        final_reasoning = llm_result.reasoning
        evidence_quote = llm_result.evidence_quote
    else:
        # Use rule engine result as fallback
        final_verdict_str = rule_verdict
        final_confidence = rule_conf
        final_reasoning = rule_reasoning
        evidence_quote = bidder_value.extracted_value
    
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
        ocr_confidence=ocr_confidence,
        hash=verdict_hash
    )
