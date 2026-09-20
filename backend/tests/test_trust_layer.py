"""Automated unit and integration tests for Stage 8 Trust Layer.

Verifies citation/evidence mapping, source document grouping, page number deduplication,
measured confidence derivation (without synthetic numerical inflation), limitations,
and API exposure.
"""

import pytest
from app.ai.models import EvidenceContext
from app.ingestion.models import DocumentChunk
from app.rag.models import RAGResponse
from app.rag.pipeline import RAGPipeline
from app.schemas.query import CitationItem
from app.search.embeddings import DeterministicEmbeddingProvider
from app.search.service import VectorSearchService
from app.search.vector_store import QdrantVectorStore
from app.trust.builder import (
    build_trust_report,
    calculate_measured_confidence,
    extract_distinct_page_numbers,
    extract_source_documents,
    generate_civic_limitations,
    map_evidence_snippets,
)
from app.trust.models import (
    EvidenceSnippetItem,
    MeasuredConfidence,
    SourceDocumentItem,
    TrustReport,
)
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient


# ---------------------------------------------------------------------------
# Unit Tests: Evidence & Citation Mapping
# ---------------------------------------------------------------------------


def test_map_evidence_snippets_from_contexts() -> None:
    """Ensure raw EvidenceContext objects map accurately to ranked EvidenceSnippetItem models."""
    contexts = [
        EvidenceContext(
            document_title="City_Budget_2024.pdf",
            page_number=14,
            chunk_id="chk_001",
            text="Parks operational expenditure is $4,250,000.",
            score=0.8923,
            metadata={"department": "Parks & Rec"},
        ),
        EvidenceContext(
            document_title="City_Budget_2024.pdf",
            page_number=18,
            chunk_id="chk_002",
            text="Community center maintenance allocation is $1,100,000.",
            score=0.8144,
            metadata={"department": "Parks & Rec"},
        ),
        EvidenceContext(
            document_title="Transit_Plan_2024.pdf",
            page_number=5,
            chunk_id="chk_003",
            text="Bus rapid transit electrification phase 1.",
            score=0.7850,
            metadata={"department": "Transportation"},
        ),
    ]

    snippets = map_evidence_snippets(contexts)

    assert len(snippets) == 3

    # Check first snippet mapping
    s1 = snippets[0]
    assert isinstance(s1, EvidenceSnippetItem)
    assert s1.snippet_id == "chk_001"
    assert s1.document_title == "City_Budget_2024.pdf"
    assert s1.page_number == 14
    assert s1.similarity_score == 0.8923
    assert s1.rank == 1
    assert s1.department == "Parks & Rec"
    assert s1.text == "Parks operational expenditure is $4,250,000."

    # Check third snippet mapping
    s3 = snippets[2]
    assert s3.snippet_id == "chk_003"
    assert s3.document_title == "Transit_Plan_2024.pdf"
    assert s3.page_number == 5
    assert s3.similarity_score == 0.7850
    assert s3.rank == 3
    assert s3.department == "Transportation"


def test_map_evidence_snippets_from_citations() -> None:
    """Ensure CitationItem objects can also be mapped to EvidenceSnippetItem models."""
    citations = [
        CitationItem(
            document_title="Public_Safety_Report.pdf",
            page_number=7,
            similarity_score=0.9105,
            excerpt="Emergency response average time dropped to 4.2 minutes.",
            chunk_id="chk_ps_07",
            department="Fire & Rescue",
        )
    ]

    snippets = map_evidence_snippets(citations)
    assert len(snippets) == 1
    assert snippets[0].snippet_id == "chk_ps_07"
    assert snippets[0].page_number == 7
    assert snippets[0].similarity_score == 0.9105
    assert snippets[0].text == "Emergency response average time dropped to 4.2 minutes."
    assert snippets[0].department == "Fire & Rescue"
    assert snippets[0].rank == 1


def test_extract_source_documents_grouping_and_page_dedup() -> None:
    """Ensure multiple snippets from same document are grouped with deduplicated, sorted pages."""
    snippets = [
        EvidenceSnippetItem(
            snippet_id="s1",
            document_title="Budget_2024.pdf",
            page_number=18,
            text="Snippet A",
            similarity_score=0.85,
            rank=1,
            department="Finance",
        ),
        EvidenceSnippetItem(
            snippet_id="s2",
            document_title="Budget_2024.pdf",
            page_number=4,
            text="Snippet B",
            similarity_score=0.88,
            rank=2,
            department="Finance",
        ),
        EvidenceSnippetItem(
            snippet_id="s3",
            document_title="Budget_2024.pdf",
            page_number=18,  # Duplicate page
            text="Snippet C",
            similarity_score=0.82,
            rank=3,
            department="Finance",
        ),
        EvidenceSnippetItem(
            snippet_id="s4",
            document_title="Zoning_Code.pdf",
            page_number=42,
            text="Snippet D",
            similarity_score=0.79,
            rank=4,
            department="Planning",
        ),
    ]

    source_docs = extract_source_documents(snippets)

    assert len(source_docs) == 2
    # Alphabetically sorted
    budget_doc = next(d for d in source_docs if d.document_title == "Budget_2024.pdf")
    zoning_doc = next(d for d in source_docs if d.document_title == "Zoning_Code.pdf")

    assert budget_doc.page_numbers == [4, 18]  # Deduplicated and sorted
    assert budget_doc.chunk_count == 3
    assert budget_doc.department == "Finance"

    assert zoning_doc.page_numbers == [42]
    assert zoning_doc.chunk_count == 1
    assert zoning_doc.department == "Planning"


def test_extract_distinct_page_numbers() -> None:
    """Ensure distinct page numbers across all sources are extracted in numerical order."""
    snippets = [
        EvidenceSnippetItem(
            snippet_id="s1",
            document_title="Doc_A.pdf",
            page_number=22,
            text="...",
            similarity_score=0.8,
            rank=1,
        ),
        EvidenceSnippetItem(
            snippet_id="s2",
            document_title="Doc_B.pdf",
            page_number=3,
            text="...",
            similarity_score=0.8,
            rank=2,
        ),
        EvidenceSnippetItem(
            snippet_id="s3",
            document_title="Doc_A.pdf",
            page_number=7,
            text="...",
            similarity_score=0.8,
            rank=3,
        ),
        EvidenceSnippetItem(
            snippet_id="s4",
            document_title="Doc_B.pdf",
            page_number=3,  # duplicate
            text="...",
            similarity_score=0.8,
            rank=4,
        ),
    ]

    pages = extract_distinct_page_numbers(snippets)
    assert pages == [3, 7, 22]


# ---------------------------------------------------------------------------
# Unit Tests: Genuine Measured Confidence (No Invented Numbers)
# ---------------------------------------------------------------------------


def test_measured_confidence_strictly_empirical() -> None:
    """Verify confidence metrics are strictly calculated from vector similarity without synthetic inflation."""
    snippets = [
        EvidenceSnippetItem(
            snippet_id="s1",
            document_title="Doc.pdf",
            page_number=1,
            text="...",
            similarity_score=0.9000,
            rank=1,
        ),
        EvidenceSnippetItem(
            snippet_id="s2",
            document_title="Doc.pdf",
            page_number=2,
            text="...",
            similarity_score=0.8000,
            rank=2,
        ),
    ]

    confidence = calculate_measured_confidence(snippets, is_insufficient_evidence=False, source_count=1)

    assert confidence.is_grounded is True
    assert confidence.evidence_count == 2
    assert confidence.mean_similarity_score == 0.8500
    assert confidence.min_similarity_score == 0.8000
    assert confidence.max_similarity_score == 0.9000
    assert confidence.score_metric == "cosine_similarity"
    assert confidence.verifiability_rating == "high"
    assert "average cosine similarity of 0.8500" in confidence.explanation
    assert "without statistical inflation" in confidence.evaluation_basis


def test_measured_confidence_insufficient_evidence() -> None:
    """Verify handling when insufficient evidence is asserted."""
    confidence = calculate_measured_confidence([], is_insufficient_evidence=True)

    assert confidence.is_grounded is False
    assert confidence.evidence_count == 0
    assert confidence.mean_similarity_score is None
    assert confidence.min_similarity_score is None
    assert confidence.max_similarity_score is None
    assert confidence.verifiability_rating == "insufficient"
    assert "asserted insufficient evidence to prevent hallucination" in confidence.explanation


def test_generate_civic_limitations() -> None:
    """Ensure civic limitations contain grounding boundaries and advisory notices."""
    limits = generate_civic_limitations(is_insufficient_evidence=False)
    assert len(limits) >= 4
    assert any("Grounding Boundary" in lim for lim in limits)
    assert any("Temporal Scope" in lim for lim in limits)
    assert any("Advisory Notice" in lim for lim in limits)

    # With insufficient evidence flag
    limits_insufficient = generate_civic_limitations(is_insufficient_evidence=True)
    assert any("Insufficient Evidence Notice" in lim for lim in limits_insufficient)


# ---------------------------------------------------------------------------
# Integration Tests: End-to-End Trust Report Generation
# ---------------------------------------------------------------------------


def test_build_trust_report_structure() -> None:
    """Verify build_trust_report generates a complete, schema-compliant TrustReport."""
    contexts = [
        EvidenceContext(
            document_title="Annual_Report.pdf",
            page_number=9,
            chunk_id="chunk_99",
            text="Total municipal grants awarded was $500,000.",
            score=0.865,
            metadata={"department": "Community Development"},
        )
    ]

    report = build_trust_report(
        answer="Total municipal grants awarded was $500,000 according to page 9.",
        evidence_items=contexts,
        model_identifier="gemini-2.5-flash",
        top_k=5,
        score_threshold=0.65,
        search_latency_ms=18.4,
        is_insufficient_evidence=False,
    )

    assert isinstance(report, TrustReport)
    assert report.answer.startswith("Total municipal grants")
    assert report.model_identifier == "gemini-2.5-flash"
    assert report.page_numbers == [9]
    assert len(report.source_documents) == 1
    assert report.source_documents[0].document_title == "Annual_Report.pdf"
    assert report.source_documents[0].page_numbers == [9]
    assert len(report.evidence_snippets) == 1
    assert report.evidence_snippets[0].similarity_score == 0.865
    assert report.retrieval_metadata.top_k == 5
    assert report.retrieval_metadata.score_threshold == 0.65
    assert report.retrieval_metadata.search_latency_ms == 18.4
    assert report.confidence.is_grounded is True
    assert report.confidence.mean_similarity_score == 0.865


def test_query_endpoint_exposes_trust_layer(client: TestClient) -> None:
    """Ensure POST /api/v1/query exposes the structured Trust Layer in API responses."""
    from app.search.dependencies import get_vector_search_service

    v_svc = get_vector_search_service()
    v_svc.index_chunks(
        [
            DocumentChunk(
                chunk_id="chk_trust_test_01",
                document_id="doc_trust_test",
                source_filename="City_Budget_Trust.pdf",
                page_number=12,
                chunk_index=0,
                text="The city allocated $3,000,000 for road repaving in 2024.",
                character_count=60,
                word_count=10,
                metadata={"department": "Public Works"},
            )
        ]
    )

    payload = {
        "question": "How much was allocated for road repaving?",
        "include_citations": True,
        "include_calculations": False,
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Validate Trust Layer in response
    assert "trust" in data
    trust = data["trust"]
    assert trust is not None

    # Required structured information checks
    assert "answer" in trust
    assert "source_documents" in trust
    assert "page_numbers" in trust
    assert "evidence_snippets" in trust
    assert "retrieval_metadata" in trust
    assert "model_identifier" in trust
    assert "limitations" in trust
    assert "confidence" in trust

    # Verify source documents structure
    assert len(trust["source_documents"]) > 0
    src_doc = next(
        (d for d in trust["source_documents"] if d["document_title"] == "City_Budget_Trust.pdf"),
        None,
    )
    assert src_doc is not None
    assert 12 in src_doc["page_numbers"]

    # Verify page numbers
    assert 12 in trust["page_numbers"]

    # Verify evidence snippet structure
    assert len(trust["evidence_snippets"]) > 0
    snip = next(
        (s for s in trust["evidence_snippets"] if s["document_title"] == "City_Budget_Trust.pdf"),
        None,
    )
    assert snip is not None
    assert snip["page_number"] == 12
    assert "road repaving" in snip["text"]
    assert "similarity_score" in snip
    assert isinstance(snip["similarity_score"], float)

    # Verify retrieval metadata
    assert trust["retrieval_metadata"]["vector_store"] == "Qdrant HNSW"
    assert trust["retrieval_metadata"]["total_retrieved_chunks"] >= 1

    # Verify model identifier
    assert trust["model_identifier"] is not None

    # Verify civic limitations
    assert len(trust["limitations"]) >= 4

    # Verify genuinely measurable confidence without fake percentages
    conf = trust["confidence"]
    assert conf["is_grounded"] is True
    assert conf["evidence_count"] >= 1
    assert conf["mean_similarity_score"] is not None
    assert conf["score_metric"] == "cosine_similarity"
    assert conf["verifiability_rating"] in ["high", "moderate"]
