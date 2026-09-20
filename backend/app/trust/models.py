"""Structured data contracts for the OpenCitizen AI Trust Layer."""

from typing import Optional
from pydantic import BaseModel, Field


class SourceDocumentItem(BaseModel):
    """Source document referenced in grounding the response."""

    document_title: str = Field(..., description="Document filename or official title")
    page_numbers: list[int] = Field(
        default_factory=list,
        description="Sorted list of distinct 1-indexed document page numbers cited",
    )
    chunk_count: int = Field(
        default=1,
        ge=1,
        description="Number of evidence chunks retrieved from this document",
    )
    department: Optional[str] = Field(
        default=None,
        description="Department or municipal agency attribution",
    )


class EvidenceSnippetItem(BaseModel):
    """Verbatim text snippet retrieved from vector store used as evidence grounding."""

    snippet_id: str = Field(..., description="Unique chunk or snippet identifier")
    document_title: str = Field(..., description="Source document title")
    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed page number where snippet appears",
    )
    text: str = Field(..., description="Verbatim text extracted from document")
    similarity_score: float = Field(
        ...,
        description="Empirical cosine similarity score (0.0 - 1.0)",
    )
    rank: int = Field(
        ...,
        ge=1,
        description="Retrieval rank among candidate chunks (1-indexed)",
    )
    department: Optional[str] = Field(
        default=None,
        description="Department attribution",
    )


class RetrievalMetadata(BaseModel):
    """Execution metadata from vector search retrieval."""

    vector_store: str = Field(
        default="Qdrant HNSW",
        description="Vector database engine and indexing technique",
    )
    top_k: int = Field(..., ge=1, description="Maximum chunks requested for retrieval")
    score_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score threshold",
    )
    total_retrieved_chunks: int = Field(
        ...,
        ge=0,
        description="Actual number of chunks meeting threshold",
    )
    search_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Vector search latency in milliseconds",
    )


class MeasuredConfidence(BaseModel):
    """Genuinely measurable confidence and explanation metadata.

    CRITICAL PRINCIPLE:
    We never invent synthetic percentage confidence scores (e.g. 98.7%) simply
    to make the UI appear impressive. Metrics are derived strictly from empirical
    vector cosine similarity, evidence presence, and source grounding state.
    """

    is_grounded: bool = Field(
        ...,
        description="Whether the answer is strictly backed by verified document evidence",
    )
    evidence_count: int = Field(
        ...,
        ge=0,
        description="Number of verified supporting evidence chunks",
    )
    mean_similarity_score: Optional[float] = Field(
        default=None,
        description="Arithmetic mean of cosine similarity scores of retrieved evidence chunks",
    )
    min_similarity_score: Optional[float] = Field(
        default=None,
        description="Minimum cosine similarity score among retrieved chunks",
    )
    max_similarity_score: Optional[float] = Field(
        default=None,
        description="Maximum cosine similarity score among retrieved chunks",
    )
    score_metric: str = Field(
        default="cosine_similarity",
        description="Empirical metric used for similarity evaluation",
    )
    verifiability_rating: str = Field(
        ...,
        description="Calibrated verifiability level: 'high', 'moderate', or 'insufficient'",
    )
    explanation: str = Field(
        ...,
        description="Transparent explanation of evidence grounding state and retrieval strength",
    )
    evaluation_basis: str = Field(
        default="Empirical vector cosine similarity and source evidence coverage without statistical inflation",
        description="Explanation of how confidence is evaluated without synthetic scores",
    )


class TrustReport(BaseModel):
    """Complete structured Trust Layer payload exposed for every AI answer."""

    answer: str = Field(..., description="Synthesized, evidence-grounded answer text")
    source_documents: list[SourceDocumentItem] = Field(
        default_factory=list,
        description="Distinct source documents cited in the answer",
    )
    page_numbers: list[int] = Field(
        default_factory=list,
        description="Distinct sorted list of all cited page numbers across sources",
    )
    evidence_snippets: list[EvidenceSnippetItem] = Field(
        default_factory=list,
        description="Verbatim evidence snippets supporting the answer with page numbers and scores",
    )
    retrieval_metadata: RetrievalMetadata = Field(
        ...,
        description="Vector search retrieval parameters and execution metrics",
    )
    model_identifier: str = Field(
        ...,
        description="Name/identifier of the AI model synthesizing the answer",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit boundaries, civic disclaimers, and data freshness limitations",
    )
    confidence: MeasuredConfidence = Field(
        ...,
        description="Genuinely measurable confidence and grounding explanation",
    )
