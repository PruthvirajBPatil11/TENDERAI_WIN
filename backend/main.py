"""
FastAPI application entry point.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.db import init_db
from backend.vector_store.qdrant_client import init_collection
from backend.api.routes import tender, bidder, evaluate, report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TenderEval AI",
    description="AI-based government tender evaluation platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(tender.router)
app.include_router(bidder.router)
app.include_router(evaluate.router)
app.include_router(report.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and vector store on startup."""
    logger.info("Starting TenderEval AI application")
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Error initializing database: {e}")
    
    try:
        init_collection()
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning(f"Error initializing vector store: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down TenderEval AI application")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "TenderEval AI"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "TenderEval AI",
        "version": "1.0.0",
        "description": "AI-based government tender evaluation platform",
        "endpoints": {
            "tender_upload": "POST /tender/upload",
            "bidder_upload": "POST /bidder/upload",
            "evaluate": "POST /evaluate",
            "get_report": "GET /report/{tender_id}/{bidder_id}",
            "export_pdf": "GET /report/{tender_id}/{bidder_id}/pdf",
            "audit_log": "GET /audit/{tender_id}",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
