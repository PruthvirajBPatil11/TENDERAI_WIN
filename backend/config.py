"""
Application configuration loaded from .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings

# Absolute path to project root — works from any working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All settings loaded from .env file."""

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    database_url: str = "sqlite:///./tender_eval.db"

    ocr_confidence_threshold: float = 0.80
    semantic_similarity_pass_threshold: float = 0.75
    semantic_similarity_review_threshold: float = 0.50

    # Data directory for uploads and outputs
    data_dir: Path = PROJECT_ROOT / "data"

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
