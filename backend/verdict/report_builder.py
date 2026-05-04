"""
Report builder - generates consolidated bidder-level reports.
"""

import logging
from backend.extraction.schemas import Verdict, BidderReport

logger = logging.getLogger(__name__)


def build_report(tender_id: str, bidder_id: str, verdicts: list[Verdict]) -> BidderReport:
    """
    Build consolidated report for a bidder from all criterion verdicts.
    
    Args:
        tender_id: ID of the tender
        bidder_id: ID of the bidder
        verdicts: List of Verdict objects for all criteria
        
    Returns:
        BidderReport object
    """
    # Determine overall verdict
    has_fail_mandatory = False
    has_manual_review = False
    
    for verdict in verdicts:
        # Check if this is a mandatory criterion failure (would need to know from Criterion)
        if verdict.verdict == "FAIL":
            # Note: We're being conservative - any FAIL leads to NOT_ELIGIBLE
            has_fail_mandatory = True
        elif verdict.verdict == "MANUAL_REVIEW":
            has_manual_review = True
    
    if has_fail_mandatory:
        overall_verdict = "NOT_ELIGIBLE"
    elif has_manual_review:
        overall_verdict = "MANUAL_REVIEW"
    else:
        overall_verdict = "ELIGIBLE"
    
    # Generate summary
    pass_count = sum(1 for v in verdicts if v.verdict == "PASS")
    fail_count = sum(1 for v in verdicts if v.verdict == "FAIL")
    review_count = sum(1 for v in verdicts if v.verdict == "MANUAL_REVIEW")
    total_count = len(verdicts)
    
    if overall_verdict == "ELIGIBLE":
        summary = f"Bidder {bidder_id} meets all mandatory criteria ({pass_count}/{total_count} passed)."
    elif overall_verdict == "NOT_ELIGIBLE":
        summary = f"Bidder {bidder_id} fails {fail_count} mandatory criterion/criteria and is not eligible."
    else:
        summary = f"Bidder {bidder_id} requires manual review ({review_count} criteria need further assessment). {pass_count} passed, {fail_count} failed."
    
    report = BidderReport(
        bidder_id=bidder_id,
        tender_id=tender_id,
        overall_verdict=overall_verdict,
        criteria_verdicts=verdicts,
        summary=summary
    )
    
    logger.info(f"Report built for {bidder_id}: {overall_verdict}")
    
    return report
