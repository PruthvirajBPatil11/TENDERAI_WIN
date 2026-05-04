"""
Verdict generator - orchestrates the complete evaluation pipeline.
"""

import logging
from backend.extraction.schemas import Criterion, BidderValue, Verdict
from backend.matching.rule_engine import apply_rule
from backend.matching.semantic_matcher import match_qualitative
from backend.matching.llm_judge import judge
from backend.matching.confidence_scorer import final_verdict

logger = logging.getLogger(__name__)


def generate_verdict(
    criterion: Criterion,
    bidder_value: BidderValue,
    bidder_context: str,
    bidder_id: str
) -> Verdict:
    """
    Generate verdict for a criterion-bidder pair by orchestrating the matching pipeline.
    
    Args:
        criterion: The criterion to evaluate
        bidder_value: Extracted value from bidder submission
        bidder_context: Surrounding context from bidder documents
        bidder_id: ID of the bidder
        
    Returns:
        Verdict object with reasoning and confidence
    """
    # Ensure bidder_id is set on bidder_value
    if not bidder_value.bidder_id:
        bidder_value.bidder_id = bidder_id
    
    ocr_confidence = bidder_value.ocr_confidence or 0.5
    
    # Step 1: Apply rule-based engine first (fastest, most deterministic)
    rule_result = apply_rule(criterion, bidder_value)
    logger.debug(f"Rule engine result for C{criterion.criterion_id}: {rule_result[0]} (conf: {rule_result[1]})")
    
    # Step 2: For qualitative criteria, also compute semantic similarity
    sem_verdict = "MANUAL_REVIEW"
    sem_score = 0.0
    sem_text = ""
    
    if criterion.criterion_type in ["technical", "compliance"]:
        sem_result = match_qualitative(criterion, [bidder_context])
        sem_verdict, sem_score, sem_text = sem_result
        logger.debug(f"Semantic match for C{criterion.criterion_id}: {sem_verdict} (score: {sem_score:.2f})")
    
    # Step 3: If results are ambiguous, use LLM judge
    llm_result = None
    rule_verdict = rule_result[0]
    
    if rule_verdict == "MANUAL_REVIEW" or (0.50 < sem_score < 0.75):
        logger.debug(f"Using LLM judge for C{criterion.criterion_id}")
        llm_result = judge(criterion, bidder_value, bidder_context)
    
    # Step 4: Combine all results into final verdict
    verdict = final_verdict(
        rule_result=rule_result,
        semantic_result=(sem_verdict, sem_score, sem_text),
        llm_result=llm_result,
        ocr_confidence=ocr_confidence,
        criterion=criterion,
        bidder_value=bidder_value
    )
    
    logger.info(f"Final verdict for {bidder_id} on C{criterion.criterion_id}: {verdict.verdict} (conf: {verdict.confidence:.2f})")
    
    return verdict
