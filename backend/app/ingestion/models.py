"""Data models for document chunks, extracted pages, and ingestion results."""

from typing import Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Structured text chunk prepared for vector embedding and provenance tracing."""

    chunk_id: str = Field(
        ...,
        description="Globally unique chunk identifier (e.g. chk_{doc_id}_p{page}_{idx})",
    )
    document_id: str = Field(
        ...,
        description="Associated parent document identifier",
    )
    source_filename: str = Field(
        ...,
        description="Original uploaded file name",
    )
    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed source page number where this chunk originates",
    )
    chunk_index: int = Field(
        ...,
        ge=0,
        description="Sequential index of this chunk within the page or document",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Cleaned, normalized text content of the chunk",
    )
    character_count: int = Field(
        ...,
        ge=1,
        description="Number of characters in the cleaned text",
    )
    word_count: int = Field(
        ...,
        ge=1,
        description="Number of words in the chunk",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional lineage and domain metadata (department, category, etc.)",
    )


class ExtractedPage(BaseModel):
    """Represents text extracted from a single PDF page with page-level integrity."""

    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed page number in the original PDF",
    )
    raw_text: str = Field(
        default="",
        description="Raw extracted text string directly from parser",
    )
    cleaned_text: str = Field(
        default="",
        description="Sanitized and normalized text string",
    )
    char_count: int = Field(
        default=0,
        description="Character count of cleaned text",
    )
    is_empty: bool = Field(
        default=False,
        description="True if page contains little or no textual content",
    )


class IngestionResult(BaseModel):
    """Overall outcome of the PDF ingestion pipeline."""

    document_id: str = Field(
        ...,
        description="Document identifier assigned to the file",
    )
    source_filename: str = Field(
        ...,
        description="Source PDF filename",
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total pages detected in the PDF document",
    )
    processed_pages: int = Field(
        ...,
        ge=0,
        description="Pages with extractable textual content",
    )
    total_chunks: int = Field(
        ...,
        ge=0,
        description="Total number of structured chunks generated",
    )
    chunks: list[DocumentChunk] = Field(
        default_factory=list,
        description="Collection of generated chunks ready for vector indexing",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered (e.g. empty or scanned pages)",
    )
    processing_time_ms: float = Field(
        default=0.0,
        description="Execution latency in milliseconds",
    )
