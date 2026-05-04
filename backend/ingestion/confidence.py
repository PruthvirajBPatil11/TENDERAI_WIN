"""
Confidence scoring for OCR fields and extracted values.
"""

import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def compute_field_confidence(words: list[dict], field_text: str) -> float:
    """
    Compute confidence score for a field by matching against OCR word list.
    
    Args:
        words: List of OCR word dicts with keys: word, confidence, bbox
        field_text: The field text to match against words
        
    Returns:
        Average confidence score (0-1), or 0.5 if no match found
    """
    if not words or not field_text:
        return 0.5
    
    # Clean the field text
    field_words = field_text.lower().split()
    
    # Try to match field words against OCR words
    matched_confidences = []
    
    for field_word in field_words:
        best_ratio = 0.0
        best_confidence = 0.0
        
        for ocr_word_dict in words:
            ocr_word = ocr_word_dict.get("word", "").lower()
            confidence = ocr_word_dict.get("confidence", 0.0)
            
            # Use sequence matching to handle slight variations
            ratio = SequenceMatcher(None, field_word, ocr_word).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_confidence = confidence
        
        # Only include matches with reasonable similarity
        if best_ratio > 0.7:
            matched_confidences.append(best_confidence)
    
    if matched_confidences:
        return sum(matched_confidences) / len(matched_confidences)
    else:
        return 0.5
