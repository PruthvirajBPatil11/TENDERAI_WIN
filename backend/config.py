"""
Application configuration loaded from environment variables or .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Absolute path to project root — works from any working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All settings loaded from environment variables or .env file."""

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tender_eval.db")

    ocr_confidence_threshold: float = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.80"))
    semantic_similarity_pass_threshold: float = float(os.getenv("SEMANTIC_SIMILARITY_PASS_THRESHOLD", "0.75"))
    semantic_similarity_review_threshold: float = float(os.getenv("SEMANTIC_SIMILARITY_REVIEW_THRESHOLD", "0.50"))

    # Data directory for uploads and outputs
    data_dir: Path = PROJECT_ROOT / "data"

    model_config = {
        "env_file": str(ENV_FILE) if ENV_FILE.exists() else None,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
