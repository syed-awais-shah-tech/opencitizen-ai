"""SQLAlchemy model for document ingestion background jobs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IngestionJob(Base):
    """Tracks background ingestion, extraction, chunking, embedding, and vector storage."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"job_{uuid.uuid4().hex[:12]}"
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="queued", nullable=False, index=True
    )  # queued, processing, completed, failed
    stage: Mapped[str] = mapped_column(
        String(50), default="queued", nullable=False
    )  # queued, extraction, chunking, embedding, vector_storage, completed, failed
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="jobs")
