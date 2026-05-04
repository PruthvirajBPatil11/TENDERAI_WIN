"""
Database connection and session management.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get a database session."""
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    from backend.database.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
