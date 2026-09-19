"""Data models for AI provider abstraction and grounded context exchange."""

from typing import Any

from pydantic import BaseModel, Field


class EvidenceContext(BaseModel):
    """Structured evidence chunk provided to the LLM for grounded answer synthesis."""

    document_title: str = Field(
        ...,
        description="Source document title or filename",
    )
    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed source page number where the chunk originates",
    )
    chunk_id: str = Field(
        ...,
        description="Unique chunk identifier in vector storage",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Verbatim text content of the evidence chunk",
    )
    score: float = Field(
        default=1.0,
        description="Vector search similarity score (0.0 to 1.0)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional chunk and document metadata",
    )


class LLMAnswer(BaseModel):
    """Answer synthesized by an AI provider with grounding verification."""

    answer_text: str = Field(
        ...,
        description="Synthesized natural language answer",
    )
    is_grounded: bool = Field(
        default=True,
        description="Indicates whether the answer is strictly grounded in supplied evidence",
    )
    is_insufficient_evidence: bool = Field(
        default=False,
        description="True if the provider concluded supplied evidence was insufficient",
    )
    model_name: str = Field(
        ...,
        description="Model identifier that produced this response",
    )
    citation_references: list[str] = Field(
        default_factory=list,
        description="List of source filenames or chunk IDs cited in the answer",
    )
