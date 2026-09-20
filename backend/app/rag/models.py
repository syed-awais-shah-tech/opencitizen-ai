from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.query import CitationItem
from app.trust.models import TrustReport


class RAGResponse(BaseModel):
    """Complete outcome of the Retrieval-Augmented Generation pipeline."""

    question: str = Field(
        ...,
        description="Original user question processed by the pipeline",
    )
    answer: str = Field(
        ...,
        description="Synthesized, evidence-grounded answer text",
    )
    citations: list[CitationItem] = Field(
        default_factory=list,
        description="Preserved citations from retrieved document chunks",
    )
    retrieved_chunks_count: int = Field(
        default=0,
        ge=0,
        description="Number of chunks retrieved from vector store",
    )
    is_insufficient_evidence: bool = Field(
        default=False,
        description="Indicates if evidence was insufficient to answer the question",
    )
    model_name: str = Field(
        ...,
        description="Name of the AI model that synthesized the response",
    )
    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Total RAG execution time in milliseconds",
    )
    trust: Optional[TrustReport] = Field(
        default=None,
        description="Structured Trust Layer audit report providing auditable provenance",
    )
