"""Pydantic schemas for municipal PDF documents and vector chunks."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class DocumentItem(BaseModel):
    """Schema representing an individual ingested municipal document."""

    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="File name or document title")
    category: str = Field(..., description="Civic topic or department categorization")
    page_count: int = Field(default=0, description="Total number of pages")
    chunk_count: int = Field(default=0, description="Extracted vector chunks")
    size_bytes: int = Field(default=0, description="Document size in bytes")
    status: Literal["ready", "processing", "pending", "failed"] = Field(
        default="ready", description="Ingestion and vectorization status"
    )
    department: str = Field(..., description="Issuing municipal agency or department")
    summary: str = Field(
        default="", description="Executive summary or description of the document"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Ingestion timestamp"
    )


class DocumentListResponse(BaseModel):
    """Response payload for listing ingested municipal documents."""

    items: list[DocumentItem] = Field(
        default_factory=list, description="Collection of ingested documents"
    )
    total: int = Field(default=0, description="Total count of documents")
