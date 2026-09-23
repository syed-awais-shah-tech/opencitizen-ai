"""Core configuration and system settings."""

import json
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    PROJECT_NAME: str = "OpenCitizen AI API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS_ORIGINS from list, JSON string, or comma-separated string."""
        origins: list[str] = []
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        origins = [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    origins = [part.strip() for part in v_str.strip("[]").split(",") if part.strip()]
            else:
                origins = [part.strip() for part in v_str.split(",") if part.strip()]
        elif isinstance(v, (list, tuple)):
            origins = [str(item).strip() for item in v if str(item).strip()]

        # Ensure local development origins are always present
        local_dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        for local_origin in local_dev_origins:
            if local_origin not in origins:
                origins.append(local_origin)
        return origins

    # Database settings (PostgreSQL for metadata)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "opencitizen"
    POSTGRES_PASSWORD: str = "opencitizen_dev_password"
    POSTGRES_DB: str = "opencitizen_app"
    DATABASE_URL: str | None = None

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construct database connection URI."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Vector Search & Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "opencitizen_documents"
    QDRANT_URL: str | None = None
    QDRANT_IN_MEMORY: bool = False

    # Embedding settings
    EMBEDDING_PROVIDER: str = "deterministic"
    EMBEDDING_DIMENSION: int = 384

    # Gemini & AI Provider settings
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_PROVIDER: str = "mock"  # "gemini" or "mock"

    # RAG Pipeline settings
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.0

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
