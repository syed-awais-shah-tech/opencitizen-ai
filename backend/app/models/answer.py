"""SQLAlchemy model for synthesized query answers."""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Answer(Base):
    """Synthesized, evidence-grounded answer generated for a user query."""

    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calculation_trace: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    query = relationship("Query", back_populates="answers")
    citations = relationship("Citation", back_populates="answer", cascade="all, delete-orphan")
