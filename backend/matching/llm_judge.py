"""
LLM-as-judge for ambiguous or complex criterion matching using Groq.
"""

import json
import logging
import hashlib
import re
from datetime import datetime
from groq import Groq
from backend.extraction.schemas import Criterion, BidderValue, Verdict
from backend.config import settings

logger = logging.getLogger(__name__)

# Initialize Groq client at module level
client = Groq(api_key=settings.groq_api_key)


def parse_verdict_block(text: str) -> dict:
    """Parse delimiter-based verdict block (100% reliable, no JSON)."""
    data = {}
    lines = text.strip().split("\n")

    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        data[key] = value

    return data


def judge(criterion: Criterion, bidder_value: BidderValue, bidder_context: str) -> Verdict:
    """
    Use Groq LLM to make a judgment verdict for ambiguous criteria.
    
    Args:
        criterion: The criterion being evaluated
        bidder_value: The extracted bidder value
        bidder_context: Relevant context from bidder documents
        
    Returns:
        Verdict object with LLM reasoning and safe fallback on error
    """
    try:
        messages = [
            {
                "role": "system",
                "content": """You are a strict government procurement eligibility evaluator.
Evaluate whether the bidder meets the criterion based ONLY on 
evidence provided. Never assume information not present in the evidence.
If evidence is insufficient, return MANUAL_REVIEW with a clear reason.

DO NOT return JSON.

Use this EXACT format:

VERDICT: PASS|FAIL|MANUAL_REVIEW
CONFIDENCE: float between 0.0 and 1.0
REASONING: clear explanation referencing specific evidence
EVIDENCE_QUOTE: exact quote from bidder document or source
SOURCE_DOCUMENT: filename string
SOURCE_PAGE: integer page number
AMBIGUITY_REASON: reason for MANUAL_REVIEW if applicable"""
            },
            {
                "role": "user",
                "content": f"""Evaluate if the bidder meets this criterion:

CRITERION:
Type: {criterion.criterion_type}
Text: {criterion.text}
Mandatory: {criterion.mandatory}
Threshold: {criterion.threshold}
Operator: {criterion.operator}
Unit: {criterion.unit}

BIDDER EVIDENCE:
Extracted Value: {bidder_value.extracted_value}
Normalised Value: {bidder_value.normalised_value}
Source Document: {bidder_value.source_document}
OCR Confidence: {bidder_value.ocr_confidence}

CONTEXT:
{bidder_context}

Make your verdict based ONLY on the information provided."""
            }
        ]

        message = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0,
            max_tokens=800,
            messages=messages
        )

        response_text = message.choices[0].message.content.strip()

        # Parse delimiter-based verdict block
        data = parse_verdict_block(response_text)
        
        # Create hash for audit trail
        verdict_str = json.dumps({
            "criterion_id": criterion.criterion_id,
            "bidder_id": bidder_value.bidder_id,
            "verdict": data.get("verdict", "MANUAL_REVIEW"),
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)
        verdict_hash = hashlib.sha256(verdict_str.encode()).hexdigest()

        # Parse confidence as float
        try:
            confidence = float(data.get("confidence", 0.5))
        except (ValueError, TypeError):
            confidence = 0.5

        # Parse page number as int
        try:
            source_page = int(data.get("source_page", 0))
        except (ValueError, TypeError):
            source_page = 0

        return Verdict(
            criterion_id=criterion.criterion_id,
            bidder_id=bidder_value.bidder_id,
            verdict=data.get("verdict", "MANUAL_REVIEW"),
            confidence=confidence,
            reasoning=data.get("reasoning", ""),
            evidence_quote=data.get("evidence_quote", ""),
            source_document=data.get("source_document", bidder_value.source_document),
            source_page=source_page or bidder_value.source_page,
            ocr_confidence=bidder_value.ocr_confidence,
            ambiguity_reason=data.get("ambiguity_reason") if data.get("verdict") == "MANUAL_REVIEW" else None,
            hash=verdict_hash
        )
    
    except Exception as e:
        logger.error(f"Error in LLM judge: {e}")
        # Return safe fallback with MANUAL_REVIEW
        verdict_str = json.dumps({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)
        verdict_hash = hashlib.sha256(verdict_str.encode()).hexdigest()
        
        return Verdict(
            criterion_id=criterion.criterion_id,
            bidder_id=bidder_value.bidder_id,
            verdict="MANUAL_REVIEW",
            confidence=0.0,
            reasoning=f"LLM evaluation failed: {str(e)}. Manual review required.",
            evidence_quote="",
            source_document=bidder_value.source_document,
            source_page=bidder_value.source_page,
            ocr_confidence=bidder_value.ocr_confidence,
            ambiguity_reason="Automated evaluation unavailable — API error",
            hash=verdict_hash
        )

