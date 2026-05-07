"""
FastAPI application entry point.
"""

import logging
import sys

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from backend.config import settings
    logger.info("Config loaded successfully")
except Exception as e:
    logger.error(f"Failed to load config: {e}", exc_info=True)
    settings = None

try:
    from backend.database.db import init_db
except Exception as e:
    logger.warning(f"Could not import init_db: {e}")
    init_db = None

try:
    from backend.vector_store.qdrant_client import init_collection
except Exception as e:
    logger.warning(f"Could not import init_collection: {e}")
    init_collection = None

try:
    from backend.api.routes import tender, bidder, evaluate, report
except Exception as e:
    logger.error(f"Failed to import routes: {e}", exc_info=True)
    tender = bidder = evaluate = report = None

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

# Include route modules safely
if tender:
    app.include_router(tender.router)
if bidder:
    app.include_router(bidder.router)
if evaluate:
    app.include_router(evaluate.router)
if report:
    app.include_router(report.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and vector store on startup."""
    logger.info("Starting TensorEval AI application")
    
    if init_db:
        try:
            init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.warning(f"Error initializing database: {e}", exc_info=True)
    else:
        logger.warning("Database initialization not available")
    
    if init_collection:
        try:
            init_collection()
            logger.info("Vector store initialized")
        except Exception as e:
            logger.warning(f"Error initializing vector store: {e}", exc_info=True)
    else:
        logger.warning("Vector store initialization not available")
    
    logger.info("Application startup complete")


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
