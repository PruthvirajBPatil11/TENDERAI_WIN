"""
Verdict generator - orchestrates the complete evaluation pipeline.
Implements criterion-specific document routing, value extraction, and rule-based evaluation.
"""

import logging
import re
import hashlib
import json
from datetime import datetime
from backend.extraction.schemas import Criterion, BidderValue, Verdict
from backend.extraction.value_normaliser import normalise_currency, normalise_date
from backend.extraction.ner_extractor import extract_entities
from backend.matching.rule_engine import apply_rule
from backend.matching.confidence_scorer import final_verdict

logger = logging.getLogger(__name__)


def _find_best_document(criterion: Criterion, bidder_docs: list) -> dict:
    """
    Find the best document for a criterion using keyword-based scoring.
    Scores documents based on criterion type and keywords in filename/content.
    
    Args:
        criterion: The criterion to match documents against
        bidder_docs: List of bidder document dicts with text, filename, and ocr_confidence
        
    Returns:
        Best matching document dict with text, filename, and ocr_confidence
    """
    if not bidder_docs:
        logger.warning(f"No documents available for criterion {criterion.criterion_id}")
        return {"text": "", "filename": "NONE", "ocr_confidence": 0.0}
    
    criterion_type = (criterion.criterion_type or "").lower()
    criterion_text = (criterion.text or "").lower()
    
    # Define keyword scores for each criterion type
    keyword_scores = {}
    
    if criterion_type == "financial":
        # Financial: +3 filename keywords
        keyword_scores = {
            "filename_keywords": ["balance", "turnover", "financial", "ca_cert", "account", "statement"],
            "filename_weight": 3,
            "text_keywords": [],
            "text_weight": 0
        }
    
    elif criterion_type == "experience":
        # Experience: +3 filename keywords
        keyword_scores = {
            "filename_keywords": ["completion", "experience", "project", "work_order", "contract", "portfolio"],
            "filename_weight": 3,
            "text_keywords": ["PROJECT", "project", "completed", "Contract"],
            "text_weight": 2
        }
    
    elif criterion_type in ["compliance", "document"] and "gst" in criterion_text:
        # GST: +5 filename, +3 text (GSTIN)
        keyword_scores = {
            "filename_keywords": ["gst", "goods_service", "goods", "service", "tax"],
            "filename_weight": 5,
            "text_keywords": ["GSTIN", "GST", "Goods and Services Tax"],
            "text_weight": 3
        }
    
    elif criterion_type in ["compliance", "technical"] and "iso" in criterion_text:
        # ISO: +5 filename, +3 text (ISO 9001)
        keyword_scores = {
            "filename_keywords": ["iso", "quality", "certification", "certified", "9001"],
            "filename_weight": 5,
            "text_keywords": ["ISO 9001", "ISO9001", "ISO", "certification"],
            "text_weight": 3
        }
    
    else:
        # Default: use document with highest OCR confidence
        best_doc = max(bidder_docs, key=lambda d: d.get("ocr_confidence", 0.0))
        logger.debug(
            f"No specific keyword scoring for {criterion_type}, "
            f"selected {best_doc.get('filename', 'unknown')} by OCR confidence"
        )
        return best_doc
    
    # Score each document
    best_score = -1
    best_doc = bidder_docs[0]
    
    for doc in bidder_docs:
        score = 0
        filename = (doc.get("filename", "") or "").lower()
        text = (doc.get("text", "") or "").lower()
        
        # Score filename keywords
        if "filename_keywords" in keyword_scores:
            for keyword in keyword_scores["filename_keywords"]:
                if keyword.lower() in filename:
                    score += keyword_scores.get("filename_weight", 1)
        
        # Score text keywords
        if "text_keywords" in keyword_scores:
            for keyword in keyword_scores["text_keywords"]:
                count = text.count(keyword.lower())
                if count > 0:
                    score += keyword_scores.get("text_weight", 1) * min(count, 3)  # Cap at 3x
        
        # Tiebreaker: higher OCR confidence
        ocr_conf = doc.get("ocr_confidence", 0.0)
        score += ocr_conf * 10  # Add OCR confidence as decimal tiebreaker
        
        logger.debug(
            f"Document scoring for {criterion_type}: "
            f"{doc.get('filename', 'unknown')} score={score:.2f}"
        )
        
        if score > best_score:
            best_score = score
            best_doc = doc
    
    logger.info(
        f"Selected document for C{criterion.criterion_id} ({criterion_type}): "
        f"{best_doc.get('filename', 'unknown')} with score {best_score:.2f}"
    )
    
    return best_doc


def _extract_value(criterion: Criterion, doc_text: str) -> tuple[str, float]:
    """
    Extract specific value from document text based on criterion type.
    Uses regex patterns and entity extraction for financial, experience, GST, and ISO criteria.
    
    Args:
        criterion: The criterion to evaluate
        doc_text: Full text extracted from the document
        
    Returns:
        Tuple of (extracted_value_str, normalised_numeric_value)
        normalised_numeric_value is None if not applicable for this criterion type
    """
    criterion_type = (criterion.criterion_type or "").lower()
    criterion_text = (criterion.text or "").lower()
    
    extracted_value = ""
    normalised_value = None
    
    # ===== FINANCIAL CRITERIA =====
    if criterion_type == "financial":
        # Find rupee amounts using regex and normalize
        entities = extract_entities(doc_text)
        
        # Try TURNOVER entities first
        if entities.get("TURNOVER"):
            turnover_text = entities["TURNOVER"][0]
            extracted_value = turnover_text
            normalised_value = normalise_currency(turnover_text)
            logger.debug(f"Financial: extracted turnover '{turnover_text}' -> {normalised_value}")
        
        # Fallback to general AMOUNT entities
        elif entities.get("AMOUNT"):
            amount_text = entities["AMOUNT"][0]
            extracted_value = amount_text
            normalised_value = normalise_currency(amount_text)
            logger.debug(f"Financial: extracted amount '{amount_text}' -> {normalised_value}")
        
        # Fallback: search for currency patterns directly
        else:
            currency_pattern = r'(?:Rs\.?\s*|₹\s*|INR\s*)[\d,]+(?:\.\d+)?(?:\s*(?:crore|lakh|Cr\.?|L\.?))?'
            matches = re.findall(currency_pattern, doc_text)
            if matches:
                extracted_value = matches[0]
                normalised_value = normalise_currency(extracted_value)
                logger.debug(f"Financial: regex found '{extracted_value}' -> {normalised_value}")
        
        if normalised_value is None:
            logger.warning(f"Financial: could not extract/normalize value from text")
    
    # ===== ISO CERTIFICATION CRITERIA (CHECK BEFORE GENERAL TECHNICAL) =====
    elif criterion_type in ["technical", "compliance"] and "iso" in criterion_text:
        entities = extract_entities(doc_text)
        
        iso_cert = None
        expiry_date = None
        
        if entities.get("ISO_CERT"):
            iso_cert = entities["ISO_CERT"][0]
            extracted_value = iso_cert
            normalised_value = 1.0
            logger.debug(f"ISO: found {iso_cert}")
        else:
            # Search for ISO pattern
            iso_pattern = r'ISO\s*9001(?::\d{4})?'
            matches = re.findall(iso_pattern, doc_text, re.IGNORECASE)
            if matches:
                iso_cert = matches[0]
                extracted_value = iso_cert
                normalised_value = 1.0
                logger.debug(f"ISO: regex found {iso_cert}")
        
        # Look for expiry date near ISO mention - use LAST date (typically "Valid Till")
        if iso_cert and entities.get("VALID_DATE"):
            # Use the LAST date which is typically "Valid Till" rather than "Valid From"
            expiry_date = entities["VALID_DATE"][-1]
            extracted_value = f"{iso_cert}, valid till {expiry_date}"
            logger.debug(f"ISO: found expiry date {expiry_date}")
        
        if not iso_cert:
            logger.warning("ISO: no ISO certification found in document")
    
    # ===== EXPERIENCE CRITERIA (FOR PROJECT/CONTRACT COUNTING) =====
    elif criterion_type in ["technical", "experience"]:
        # Count PROJECT occurrences or Contract lines
        entities = extract_entities(doc_text)
        
        # Count project mentions
        project_count = doc_text.lower().count("project")
        contract_count = doc_text.lower().count("contract")
        completed_count = doc_text.lower().count("completed")
        
        extracted_value = f"projects: {project_count}, contracts: {contract_count}, completed: {completed_count}"
        # Use maximum count as normalized value
        normalised_value = float(max(project_count, contract_count, completed_count))
        
        logger.debug(
            f"Experience: found {project_count} projects, {contract_count} contracts, "
            f"{completed_count} completed -> normalized={normalised_value}"
        )
    
    # ===== GST CRITERIA =====
    elif criterion_type in ["compliance", "document"] and "gst" in criterion_text:
        entities = extract_entities(doc_text)
        
        if entities.get("GST_NO"):
            gstin = entities["GST_NO"][0]
            extracted_value = gstin
            # GSTIN is valid if it exists (just set a high value)
            normalised_value = 1.0
            logger.debug(f"GST: found GSTIN {gstin}")
        else:
            # Search for GSTIN pattern directly
            gstin_pattern = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}'
            matches = re.findall(gstin_pattern, doc_text)
            if matches:
                extracted_value = matches[0]
                normalised_value = 1.0
                logger.debug(f"GST: regex found GSTIN {extracted_value}")
            else:
                logger.warning("GST: no GSTIN found in document")
    
    # ===== DEFAULT: NO SPECIFIC EXTRACTION =====
    else:
        logger.debug(f"No specific extraction logic for criterion type '{criterion_type}'")
        extracted_value = doc_text[:500]  # First 500 chars as fallback
        normalised_value = None
    
    return (extracted_value, normalised_value)


def generate_verdict(
    criterion: Criterion,
    bidder_docs: list,
    bidder_id: str
) -> Verdict:
    """
    Generate verdict for a criterion-bidder pair using best matching document.
    
    Pipeline:
    1. Find best document using keyword scoring
    2. Extract value from document text using criterion-specific logic
    3. Apply rule engine for rule-based evaluation
    4. Combine with OCR confidence to produce final verdict
    5. Return Verdict object with reasoning, source, and confidence
    
    Args:
        criterion: The criterion to evaluate (Criterion object)
        bidder_docs: List of bidder documents (each with text, filename, ocr_confidence, doc_type, extraction_method)
        bidder_id: ID of the bidder being evaluated
        
    Returns:
        Verdict object with:
        - criterion_id, bidder_id
        - verdict: "PASS", "FAIL", or "MANUAL_REVIEW"
        - confidence: 0.0 to 1.0 score
        - reasoning: explanation of the verdict
        - source_document: filename of document used
        - source_page: page number
        - hash: SHA-256 hash for audit trail
        - ocr_confidence: confidence of the OCR extraction
        - evidence_quote: relevant quote from document
    
    Logs:
    - INFO: verdict generation start and result
    - DEBUG: document selection, value extraction, rule application
    - WARNING: missing documents, extraction failures
    """
    
    logger.info(f"Generating verdict for {bidder_id} on criterion {criterion.criterion_id}")
    
    # Step 1: Find best document using keyword scoring
    best_doc = _find_best_document(criterion, bidder_docs)
    
    if not best_doc.get("text"):
        logger.warning(f"No document text found for {bidder_id} on {criterion.criterion_id}")
        return Verdict(
            criterion_id=criterion.criterion_id,
            bidder_id=bidder_id,
            verdict="MANUAL_REVIEW",
            confidence=0.0,
            reasoning="No document text available for evaluation",
            evidence_quote="",
            source_document=best_doc.get("filename", "NONE"),
            source_page=1,
            ocr_confidence=0.0,
            ambiguity_reason="Missing document content"
        )
    
    doc_text = best_doc.get("text", "")
    ocr_confidence = best_doc.get("ocr_confidence", 0.99)
    doc_filename = best_doc.get("filename", "unknown")
    
    logger.debug(
        f"Using document: {doc_filename} "
        f"(type: {best_doc.get('doc_type')}, "
        f"confidence: {ocr_confidence:.3f})"
    )
    
    # Step 2: Extract value using criterion-specific logic
    extracted_value_str, normalised_value = _extract_value(criterion, doc_text)
    
    logger.debug(
        f"Extracted value: '{extracted_value_str[:100]}...' "
        f"-> normalized: {normalised_value}"
    )
    
    # Step 3: Create BidderValue for rule engine
    bidder_value = BidderValue(
        criterion_id=criterion.criterion_id,
        bidder_id=bidder_id,
        extracted_value=extracted_value_str,
        normalised_value=normalised_value,
        source_document=doc_filename,
        source_page=1,
        extraction_method=best_doc.get("extraction_method", "unknown"),
        ocr_confidence=ocr_confidence
    )
    
    # Step 4: Apply rule engine
    rule_verdict_str, rule_confidence = apply_rule(criterion, bidder_value)
    
    logger.debug(
        f"Rule engine result: {rule_verdict_str} "
        f"(confidence: {rule_confidence:.2f})"
    )
    
    # Step 5: Combine with OCR confidence for final verdict
    verdict = final_verdict(
        rule_result=(rule_verdict_str, rule_confidence),
        ocr_confidence=ocr_confidence,
        criterion=criterion,
        bidder_value=bidder_value
    )
    
    # Set OCR confidence on verdict object
    verdict.ocr_confidence = ocr_confidence
    verdict.source_document = doc_filename
    
    logger.info(
        f"Final verdict for {bidder_id} on C{criterion.criterion_id}: "
        f"{verdict.verdict} (confidence: {verdict.confidence:.2f}, "
        f"ocr_confidence: {ocr_confidence:.3f})"
    )
    
    return verdict

