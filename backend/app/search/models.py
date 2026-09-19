"""Data models for vector search results, queries, and index operations."""

from typing import Any

from pydantic import BaseModel, Field


class VectorSearchResult(BaseModel):
    """Represents a retrieved document chunk with similarity score and preserved provenance."""

    chunk_id: str = Field(
        ...,
        description="Unique chunk identifier",
    )
    document_id: str = Field(
        ...,
        description="Parent document identifier",
    )
    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed source page number",
    )
    source_filename: str = Field(
        ...,
        description="Original uploaded document filename",
    )
    original_text: str = Field(
        ...,
        description="Original extracted text content of the chunk",
    )
    score: float = Field(
        ...,
        description="Similarity or relevance score computed by the vector store",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional lineage or domain metadata attached to the chunk",
    )


class VectorIndexResult(BaseModel):
    """Summary outcome of indexing chunks into a vector collection."""

    indexed_count: int = Field(
        default=0,
        ge=0,
        description="Number of vector points successfully indexed",
    )
    collection_name: str = Field(
        ...,
        description="Name of the vector collection where points were stored",
    )
    document_ids: list[str] = Field(
        default_factory=list,
        description="List of distinct document IDs represented in the indexed batch",
    )
    duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Time taken to generate embeddings and index points in milliseconds",
    )


class SearchQuery(BaseModel):
    """Semantic search query request parameters."""

    query: str = Field(
        ...,
        min_length=1,
        description="User search query string",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of top similar results to return",
    )
    score_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional minimum cosine similarity score threshold",
    )
    document_id: str | None = Field(
        default=None,
        description="Optional document ID to restrict search scope",
    )
