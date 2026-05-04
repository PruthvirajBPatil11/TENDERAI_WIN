"""
Semantic similarity matching for qualitative criteria using sentence transformers.
"""

import logging
from sentence_transformers import SentenceTransformer
from backend.extraction.schemas import Criterion
from backend.config import settings
import numpy as np

logger = logging.getLogger(__name__)

# Global embedder
_embedder = None


def get_embedder() -> SentenceTransformer:
    """Get or create the sentence transformer model."""
    global _embedder
    if _embedder is None:
        try:
            _embedder = SentenceTransformer('all-mpnet-base-v2')
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            return None
    return _embedder


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts.
    
    Args:
        text_a: First text
        text_b: Second text
        
    Returns:
        Similarity score from 0 to 1
    """
    if not text_a or not text_b:
        return 0.0
    
    try:
        embedder = get_embedder()
        if embedder is None:
            logger.warning("Embedder not available, returning 0.0")
            return 0.0
        
        # Encode texts
        embeddings_a = embedder.encode([text_a], convert_to_tensor=False)
        embeddings_b = embedder.encode([text_b], convert_to_tensor=False)
        
        # Check for NaN or invalid embeddings
        if embeddings_a is None or embeddings_b is None or \
           np.isnan(embeddings_a).any() or np.isnan(embeddings_b).any():
            logger.warning("Invalid embeddings (NaN detected), returning 0.0")
            return 0.0
        
        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(embeddings_a, embeddings_b)[0][0]
        
        # Ensure valid range [0, 1]
        if np.isnan(similarity):
            logger.warning(f"Similarity calculation returned NaN")
            return 0.0
        
        similarity = max(0.0, min(1.0, float(similarity)))
        logger.debug(f"Similarity between '{text_a[:50]}...' and '{text_b[:50]}...': {similarity:.3f}")
        
        return similarity
    except Exception as e:
        logger.warning(f"Error computing semantic similarity: {e}")
        logger.debug(f"text_a: {text_a[:100]}")
        logger.debug(f"text_b: {text_b[:100]}")
        return 0.0


def match_qualitative(criterion: Criterion, bidder_texts: list[str]) -> tuple[str, float, str]:
    """
    Match qualitative criterion against bidder texts using semantic similarity.
    
    Args:
        criterion: The criterion to match
        bidder_texts: List of text snippets from bidder documents
        
    Returns:
        Tuple of (verdict_suggestion, similarity_score, best_matching_text)
    """
    if not bidder_texts:
        return ("FAIL", 0.0, "")
    
    criterion_text = criterion.text
    
    # Compute similarity against all bidder texts
    similarities = []
    for bidder_text in bidder_texts:
        sim = semantic_similarity(criterion_text, bidder_text)
        similarities.append((sim, bidder_text))
    
    # Get best match
    best_score, best_text = max(similarities, key=lambda x: x[0])
    
    # Make verdict based on threshold
    if best_score > settings.semantic_similarity_pass_threshold:
        verdict = "PASS"
    elif best_score < settings.semantic_similarity_review_threshold:
        verdict = "FAIL"
    else:
        verdict = "MANUAL_REVIEW"
    
    return (verdict, best_score, best_text)
