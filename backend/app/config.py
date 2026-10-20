"""
Centralized configuration loaded from environment variables.
"""
import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_GENERATION_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # Retrieval / RAG tuning
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.55
    CHUNK_SIZE: int = 800  # characters per chunk
    CHUNK_OVERLAP: int = 150

    # Storage & Persistence
    UPLOAD_DIR: str = "./data/uploads"
    VECTOR_DB_DIR: str = "./data/chroma"
    DATABASE_URL: str = "sqlite:///./data/documind.db"
    MAX_FILE_SIZE_MB: int = 20

    # OCR Settings
    OCR_MIN_CHARS: int = 20
    OCR_DPI: int = 200

    # Security & Rate Limiting
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    RATE_LIMIT_PER_MINUTE: int = 30
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def ensure_directories(self) -> None:
        """Ensure necessary storage directories exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.VECTOR_DB_DIR, exist_ok=True)
        if self.DATABASE_URL.startswith("sqlite:///"):
            db_path = self.DATABASE_URL.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)


settings = Settings()
settings.ensure_directories()
