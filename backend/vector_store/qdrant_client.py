"""
Qdrant vector store client for semantic search over criteria.
"""

import logging
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from backend.extraction.schemas import Criterion
from backend.config import settings

logger = logging.getLogger(__name__)

# Global Qdrant client and embedder
_qdrant_client = None
_embedder = None


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=5.0
        )
    return _qdrant_client


def get_embedder() -> SentenceTransformer:
    """Get or create sentence transformer model."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer('all-mpnet-base-v2')
    return _embedder


def init_collection(collection_name: str = "criteria") -> None:
    """Initialize Qdrant collection if it doesn't exist."""
    try:
        client = get_qdrant_client()
        
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
        else:
            logger.info(f"Collection {collection_name} already exists")
    
    except Exception as e:
        logger.error(f"Error initializing Qdrant collection: {e}")
        raise


def store_criterion(criterion: Criterion, collection_name: str = "criteria") -> None:
    """Store a criterion embedding in Qdrant."""
    try:
        client = get_qdrant_client()
        embedder = get_embedder()
        
        # Generate embedding
        embedding = embedder.encode(criterion.text, convert_to_tensor=False).tolist()
        
        # Create point
        point = PointStruct(
            id=hash(criterion.criterion_id) % (2**31),  # Use hash for numeric ID
            vector=embedding,
            payload={
                "criterion_id": criterion.criterion_id,
                "text": criterion.text,
                "type": criterion.criterion_type,
                "mandatory": criterion.mandatory,
                "threshold": criterion.threshold,
                "operator": criterion.operator,
                "unit": criterion.unit
            }
        )
        
        # Upsert to collection
        client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        
        logger.debug(f"Stored criterion {criterion.criterion_id} in vector store")
    
    except Exception as e:
        logger.error(f"Error storing criterion in vector store: {e}")
        raise


def search_similar(query_text: str, top_k: int = 5, collection_name: str = "criteria") -> list[dict]:
    """Search for similar criteria by semantic similarity."""
    try:
        client = get_qdrant_client()
        embedder = get_embedder()
        
        # Generate query embedding
        query_embedding = embedder.encode(query_text, convert_to_tensor=False).tolist()
        
        # Search
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Convert results
        results = []
        for result in search_results:
            results.append({
                "criterion_id": result.payload.get("criterion_id"),
                "text": result.payload.get("text"),
                "type": result.payload.get("type"),
                "score": result.score
            })
        
        logger.debug(f"Found {len(results)} similar criteria")
        return results
    
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return []
