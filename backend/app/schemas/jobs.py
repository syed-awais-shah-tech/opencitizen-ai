"""Pydantic schemas for document ingestion background jobs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job lifecycle statuses."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStage(str, Enum):
    """Pipeline stages executed by the background worker."""

    QUEUED = "queued"
    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    VECTOR_STORAGE = "vector_storage"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJobResponse(BaseModel):
    """Schema representing an ingestion processing job."""

    id: str = Field(..., description="Unique job identifier")
    document_id: str = Field(..., description="Associated document identifier")
    status: Literal["queued", "processing", "completed", "failed"] = Field(
        ..., description="Current status: queued, processing, completed, failed"
    )
    stage: str = Field(
        default="queued",
        description="Current pipeline stage: queued, extraction, chunking, embedding, vector_storage, completed, failed",
    )
    progress_pct: int = Field(
        default=0, ge=0, le=100, description="Processing progress percentage (0-100)"
    )
    total_pages: int = Field(default=0, description="Total pages detected")
    processed_pages: int = Field(default=0, description="Pages successfully extracted")
    total_chunks: int = Field(default=0, description="Total chunks created and indexed")
    error_message: Optional[str] = Field(default=None, description="Error details if failed")
    processing_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last status update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class DocumentStatusResponse(BaseModel):
    """Quick status check for a document and its active job."""

    document_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    status: str = Field(..., description="Document status: queued, processing, completed, failed, ready")
    job_id: Optional[str] = Field(default=None, description="Active or latest job identifier")
    job_status: Optional[str] = Field(default=None, description="Latest job status")
    stage: Optional[str] = Field(default=None, description="Latest processing stage")
    progress_pct: int = Field(default=0, description="Processing progress percentage")
    total_pages: int = Field(default=0, description="Total pages")
    chunk_count: int = Field(default=0, description="Total chunks indexed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
