"""Data models for OpenCitizen AI benchmark dataset and evaluation results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class BenchmarkItem(BaseModel):
    """Represents a single benchmark question with ground-truth criteria and evidence."""

    question_id: str = Field(
        ...,
        description="Unique identifier for the benchmark item (e.g. BENCH-001)",
    )
    question: str = Field(
        ...,
        min_length=3,
        description="Natural language question submitted to the system",
    )
    category: str = Field(
        ...,
        description="Domain category (e.g. budget, healthcare, zoning, transit, water, unsupported)",
    )
    expected_answer: str = Field(
        ...,
        description="Gold standard or reference answer text",
    )
    answer_criteria: list[str] = Field(
        default_factory=list,
        description="Mandatory factual elements, keywords, or numerical values that must appear in the answer",
    )
    negative_criteria: list[str] = Field(
        default_factory=list,
        description="Forbidden terms or hallucinated assertions that must NOT appear in the answer",
    )
    expected_source_documents: list[str] = Field(
        default_factory=list,
        description="List of expected source filenames (e.g. city_annual_budget_2024.pdf)",
    )
    expected_chunk_ids: list[str] = Field(
        default_factory=list,
        description="List of expected chunk IDs that contain relevant evidence",
    )
    expected_evidence_snippets: list[str] = Field(
        default_factory=list,
        description="Key ground-truth text excerpts expected to substantiate the answer",
    )
    is_refusal_expected: bool = Field(
        default=False,
        description="True if the inquiry is out-of-scope or unsupported, requiring an evidence refusal disclaimer",
    )


class QueryEvaluationResult(BaseModel):
    """Detailed evaluation outcome for an individual benchmark inquiry."""

    question_id: str
    question: str
    category: str
    is_refusal_expected: bool

    # Actual system outputs
    actual_answer: str
    actual_source_documents: list[str] = Field(default_factory=list)
    actual_chunk_ids: list[str] = Field(default_factory=list)
    cited_document_titles: list[str] = Field(default_factory=list)
    is_insufficient_evidence: bool = False

    # Metric scores [0.0, 1.0]
    retrieval_success: bool
    chunk_recall: float = Field(ge=0.0, le=1.0)
    document_precision: float = Field(ge=0.0, le=1.0)

    citation_correctness: float = Field(ge=0.0, le=1.0)
    citation_precision: float = Field(ge=0.0, le=1.0)
    citation_recall: float = Field(ge=0.0, le=1.0)

    answer_correctness: float = Field(ge=0.0, le=1.0)
    criteria_match_rate: float = Field(ge=0.0, le=1.0)
    token_f1: float = Field(ge=0.0, le=1.0)

    unsupported_claims_count: int = Field(ge=0)
    has_unsupported_claims: bool = False
    unsupported_claims_detail: list[str] = Field(default_factory=list)

    # Latencies in milliseconds
    search_latency_ms: float = Field(ge=0.0)
    total_latency_ms: float = Field(ge=0.0)


class OverallMetrics(BaseModel):
    """Aggregated benchmark performance metrics."""

    total_queries: int = Field(ge=0)
    retrieval_success_rate: float = Field(ge=0.0, le=1.0)
    mean_chunk_recall: float = Field(ge=0.0, le=1.0)
    mean_document_precision: float = Field(ge=0.0, le=1.0)

    citation_correctness_score: float = Field(ge=0.0, le=1.0)
    mean_citation_precision: float = Field(ge=0.0, le=1.0)
    mean_citation_recall: float = Field(ge=0.0, le=1.0)

    answer_correctness_score: float = Field(ge=0.0, le=1.0)
    mean_criteria_match_rate: float = Field(ge=0.0, le=1.0)
    mean_token_f1: float = Field(ge=0.0, le=1.0)

    unsupported_claims_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion of answers that contain at least one unsupported factual claim",
    )
    total_unsupported_claims: int = Field(ge=0)
    refusal_accuracy: float = Field(
        ge=0.0,
        le=1.0,
        description="Accuracy in correctly returning insufficient evidence on out-of-scope inquiries",
    )

    # Latency percentiles in milliseconds
    mean_latency_ms: float = Field(ge=0.0)
    p50_latency_ms: float = Field(ge=0.0)
    p90_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    min_latency_ms: float = Field(ge=0.0)
    max_latency_ms: float = Field(ge=0.0)


class BenchmarkReport(BaseModel):
    """Complete machine-readable evaluation report containing metadata and results."""

    report_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    benchmark_version: str = "1.0.0"
    retrieval_mode: str = "hybrid"
    top_k: int = 5
    score_threshold: Optional[float] = None
    overall_metrics: OverallMetrics
    per_query_results: list[QueryEvaluationResult]
