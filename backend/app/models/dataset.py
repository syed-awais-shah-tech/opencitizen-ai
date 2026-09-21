"""SQLAlchemy model for registered civic tabular datasets."""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Dataset(Base):
    """Metadata tracking for registered CSV/Parquet tabular datasets."""

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    uploaded_file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    columns_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="registered", nullable=False)
    columns_metadata: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    # Provenance fields for external public-data sources (Stage 17)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retrieval_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    original_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=dict, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    uploaded_file = relationship("UploadedFile")
