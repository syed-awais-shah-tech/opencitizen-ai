"""Comprehensive test suite for Stage 13 Hybrid Retrieval Architecture.

Tests cover:
1. BM25Index tokenization, indexing, scoring, document-level filtering, and deletion.
2. ReciprocalRankFusionReranker mathematical scoring, weight configuration, and metadata preservation.
3. VectorSearchService integration with dual indexing and mode selection.
4. Empirical benchmark evaluation proving hybrid retrieval outperforms semantic-only retrieval.
"""

import pytest
from app.ingestion.models import DocumentChunk
from app.search.embeddings import DeterministicEmbeddingProvider
from app.search.evaluation import (
    evaluate_retrieval,
    get_evaluation_corpus,
    get_evaluation_queries,
    run_standalone_evaluation,
)
from app.search.lexical import BM25Index, tokenize
from app.search.models import VectorSearchResult
from app.search.reranker import ReciprocalRankFusionReranker
from app.search.service import VectorSearchService
from app.search.vector_store import QdrantVectorStore
from qdrant_client import QdrantClient


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    """Diverse civic chunks with municipal identifiers, numbers, and conceptual content."""
    return [
        DocumentChunk(
            chunk_id="chk_civic_001",
            document_id="doc-civic-1",
            source_filename="city_ordinance_2024.pdf",
            page_number=1,
            chunk_index=0,
            text=(
                "Under Ordinance ORD-2024-99, City Council approves zoning variance for "
                "downtown mixed-use residential development with max height 75 feet."
            ),
            character_count=154,
            word_count=21,
            metadata={"code": "ORD-2024-99", "zone": "commercial"},
        ),
        DocumentChunk(
            chunk_id="chk_civic_002",
            document_id="doc-civic-1",
            source_filename="city_ordinance_2024.pdf",
            page_number=2,
            chunk_index=1,
            text=(
                "Project PRJ-011 allocates 3.2 million dollars for protected bicycle lane "
                "construction along Main Street and Broadway Corridor."
            ),
            character_count=144,
            word_count=20,
            metadata={"code": "PRJ-011", "dept": "Transportation"},
        ),
        DocumentChunk(
            chunk_id="chk_civic_003",
            document_id="doc-civic-2",
            source_filename="health_advisory.pdf",
            page_number=3,
            chunk_index=0,
            text=(
                "Lead water pipe remediation under guideline EPA-502.2 mandates replacing all "
                "lead service lines within 500 feet of public elementary schools."
            ),
            character_count=165,
            word_count=22,
            metadata={"guideline": "EPA-502.2", "safety": "critical"},
        ),
    ]


@pytest.fixture
def hybrid_search_service() -> VectorSearchService:
    """Isolated in-memory VectorSearchService configured with deterministic embeddings."""
    qdrant = QdrantClient(location=":memory:")
    embed_provider = DeterministicEmbeddingProvider(dimension=64)
    store = QdrantVectorStore(
        client=qdrant,
        default_collection="test_hybrid_collection",
        dimension=64,
    )
    return VectorSearchService(
        vector_store=store,
        embedding_provider=embed_provider,
        collection_name="test_hybrid_collection",
    )


# ==============================================================================
# 1. BM25Index Unit Tests
# ==============================================================================


def test_bm25_tokenize_preserves_civic_identifiers() -> None:
    """Test tokenizer preserves hyphenated resolution codes, contract numbers, and acronyms."""
    text = "Reviewing Resolution RES-2024-089, contract CTR-2023-142, and project PRJ-011!"
    tokens = tokenize(text)

    assert "res-2024-089" in tokens
    assert "ctr-2023-142" in tokens
    assert "prj-011" in tokens
    assert "reviewing" in tokens
    # Stopwords like 'and' should be removed
    assert "and" not in tokens


def test_bm25_tokenize_all_stopwords_fallback() -> None:
    """Test tokenizer gracefully preserves tokens when text consists entirely of stopwords."""
    text = "to be or not to be"
    tokens = tokenize(text)
    assert len(tokens) > 0
    assert "to" in tokens
    assert "be" in tokens


def test_bm25_indexing_and_statistics(sample_chunks: list[DocumentChunk]) -> None:
    """Test BM25 inverted index builds term frequencies and corpus stats properly."""
    index = BM25Index()
    indexed_count = index.index_chunks(sample_chunks)

    assert indexed_count == 3
    assert index.count() == 3
    assert index.avg_doc_len > 0
    assert "ord-2024-99" in index.inverted_index
    assert "chk_civic_001" in index.inverted_index["ord-2024-99"]


def test_bm25_search_exact_match(sample_chunks: list[DocumentChunk]) -> None:
    """Test BM25 search returns exact matching chunk at rank 1."""
    index = BM25Index()
    index.index_chunks(sample_chunks)

    results = index.search("ORD-2024-99 zoning variance", top_k=2)
    assert len(results) >= 1
    top_hit = results[0]
    assert top_hit.chunk_id == "chk_civic_001"
    assert top_hit.source_filename == "city_ordinance_2024.pdf"
    assert top_hit.metadata["retrieval_method"] == "lexical"
    assert top_hit.score > 0.0


def test_bm25_search_filter_by_document_id(sample_chunks: list[DocumentChunk]) -> None:
    """Test BM25 search restricts results when filter_document_id is provided."""
    index = BM25Index()
    index.index_chunks(sample_chunks)

    results = index.search(
        "public elementary schools",
        top_k=5,
        filter_document_id="doc-civic-1",  # doc-civic-2 has this text, doc-civic-1 does not
    )
    assert results == []

    valid_results = index.search(
        "public elementary schools",
        top_k=5,
        filter_document_id="doc-civic-2",
    )
    assert len(valid_results) == 1
    assert valid_results[0].chunk_id == "chk_civic_003"


def test_bm25_delete_document(sample_chunks: list[DocumentChunk]) -> None:
    """Test deleting document removes its chunks from inverted index and resets stats."""
    index = BM25Index()
    index.index_chunks(sample_chunks)
    assert index.count() == 3

    deleted = index.delete_document("doc-civic-1")
    assert deleted == 2
    assert index.count() == 1

    # Searching for deleted content returns empty
    results = index.search("ORD-2024-99", top_k=1)
    assert results == []

    # Surviving document remains searchable
    surviving = index.search("EPA-502.2", top_k=1)
    assert len(surviving) == 1
    assert surviving[0].chunk_id == "chk_civic_003"


def test_bm25_empty_query_and_clear(sample_chunks: list[DocumentChunk]) -> None:
    """Test edge cases: blank query string and index clearing."""
    index = BM25Index()
    index.index_chunks(sample_chunks)

    assert index.search("") == []
    assert index.search("   ") == []

    index.clear()
    assert index.count() == 0
    assert index.search("ORD-2024-99") == []


# ==============================================================================
# 2. ReciprocalRankFusionReranker Unit Tests
# ==============================================================================


def test_rrf_reranking_formula_precision() -> None:
    """Test RRF reranker mathematical formula with known candidate positions."""
    reranker = ReciprocalRankFusionReranker(
        rrf_k=60, weight_semantic=0.6, weight_lexical=0.4
    )

    sem_res = [
        VectorSearchResult(
            chunk_id="chunk_A",
            document_id="doc-1",
            page_number=1,
            source_filename="a.pdf",
            original_text="text a",
            score=0.90,
        ),
        VectorSearchResult(
            chunk_id="chunk_B",
            document_id="doc-1",
            page_number=2,
            source_filename="b.pdf",
            original_text="text b",
            score=0.70,
        ),
    ]

    lex_res = [
        VectorSearchResult(
            chunk_id="chunk_B",
            document_id="doc-1",
            page_number=2,
            source_filename="b.pdf",
            original_text="text b",
            score=12.0,
        ),
        VectorSearchResult(
            chunk_id="chunk_C",
            document_id="doc-2",
            page_number=1,
            source_filename="c.pdf",
            original_text="text c",
            score=5.0,
        ),
    ]

    # Expected RRF scores:
    # chunk_A: rank_sem=1 -> 0.6 / (60 + 1) = 0.6 / 61 = ~0.009836
    # chunk_B: rank_sem=2, rank_lex=1 -> 0.6 / (60 + 2) + 0.4 / (60 + 1) = 0.6/62 + 0.4/61 = ~0.009677 + 0.006557 = ~0.016235
    # chunk_C: rank_lex=2 -> 0.4 / (60 + 2) = 0.4 / 62 = ~0.006452
    # chunk_B should be ranked first because it appears in both channels!

    reranked = reranker.rerank(sem_res, lex_res, top_k=3)
    assert len(reranked) == 3
    assert reranked[0].chunk_id == "chunk_B"
    assert reranked[1].chunk_id == "chunk_A"
    assert reranked[2].chunk_id == "chunk_C"

    # Verify retrieval methods recorded in metadata
    assert reranked[0].metadata["retrieval_method"] == "hybrid"
    assert reranked[1].metadata["retrieval_method"] == "semantic_only"
    assert reranked[2].metadata["retrieval_method"] == "lexical_only"


def test_rrf_metadata_provenance_preservation() -> None:
    """Test all source metadata and provenance fields are preserved without mutation."""
    reranker = ReciprocalRankFusionReranker()

    sem_res = [
        VectorSearchResult(
            chunk_id="chk_prov_123",
            document_id="doc-municipal-audit",
            page_number=14,
            source_filename="city_audit_fy24.pdf",
            original_text="Audit finding: unallocated surplus of 4.1M.",
            score=0.88,
            metadata={"audit_division": "Finance", "auditor_id": "AUD-99"},
        )
    ]

    reranked = reranker.rerank(sem_res, [], top_k=1)
    assert len(reranked) == 1
    hit = reranked[0]

    assert hit.chunk_id == "chk_prov_123"
    assert hit.document_id == "doc-municipal-audit"
    assert hit.page_number == 14
    assert hit.source_filename == "city_audit_fy24.pdf"
    assert hit.original_text == "Audit finding: unallocated surplus of 4.1M."
    assert hit.metadata["audit_division"] == "Finance"
    assert hit.metadata["auditor_id"] == "AUD-99"
    assert "retrieval_meta" in hit.metadata


def test_rrf_score_threshold_filtering() -> None:
    """Test score_threshold filters low scoring candidates after fusion."""
    reranker = ReciprocalRankFusionReranker()

    sem_res = [
        VectorSearchResult(
            chunk_id="chk_high",
            document_id="doc-1",
            page_number=1,
            source_filename="doc.pdf",
            original_text="high relevance",
            score=0.95,
        ),
        VectorSearchResult(
            chunk_id="chk_low",
            document_id="doc-1",
            page_number=2,
            source_filename="doc.pdf",
            original_text="marginal relevance",
            score=0.10,
        ),
    ]

    # Calibrated score for chk_high will be 0.95 * 0.6 = 0.57
    # Calibrated score for chk_low will be 0.10 * 0.6 = 0.06
    filtered = reranker.rerank(sem_res, [], top_k=5, score_threshold=0.30)
    assert len(filtered) == 1
    assert filtered[0].chunk_id == "chk_high"


# ==============================================================================
# 3. VectorSearchService Integration Tests
# ==============================================================================


def test_service_indexes_both_vector_and_lexical(
    hybrid_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test index_chunks populates both Qdrant vector store and BM25 index."""
    result = hybrid_search_service.index_chunks(sample_chunks)

    assert result.indexed_count == 3
    assert hybrid_search_service.count() == 3
    assert hybrid_search_service.lexical_index.count() == 3


def test_service_search_modes(
    hybrid_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test VectorSearchService in hybrid (default), semantic, and lexical modes."""
    hybrid_search_service.index_chunks(sample_chunks)

    # 1. Default mode is hybrid
    hybrid_hits = hybrid_search_service.search("ORD-2024-99 zoning height", top_k=1)
    assert len(hybrid_hits) == 1
    assert hybrid_hits[0].chunk_id == "chk_civic_001"
    assert hybrid_hits[0].metadata["retrieval_method"] in ["hybrid", "lexical_only"]

    # 2. Semantic mode
    sem_hits = hybrid_search_service.search(
        "protected bicycle infrastructure", top_k=1, mode="semantic"
    )
    assert len(sem_hits) == 1
    assert sem_hits[0].chunk_id == "chk_civic_002"

    # 3. Lexical mode
    lex_hits = hybrid_search_service.search("EPA-502.2", top_k=1, mode="lexical")
    assert len(lex_hits) == 1
    assert lex_hits[0].chunk_id == "chk_civic_003"
    assert lex_hits[0].metadata["retrieval_method"] == "lexical"


def test_service_delete_document_cleans_both(
    hybrid_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test document deletion purges records from both vector store and BM25 index."""
    hybrid_search_service.index_chunks(sample_chunks)
    assert hybrid_search_service.count() == 3
    assert hybrid_search_service.lexical_index.count() == 3

    hybrid_search_service.delete_document("doc-civic-1")
    assert hybrid_search_service.count() == 1
    assert hybrid_search_service.lexical_index.count() == 1

    # Deleted chunks from doc-civic-1 must never be returned in search
    hybrid_hits = hybrid_search_service.search("ORD-2024-99")
    for hit in hybrid_hits:
        assert hit.document_id != "doc-civic-1"

    # Lexical searches for deleted codes return strictly empty
    assert hybrid_search_service.search_lexical("ORD-2024-99") == []
    assert hybrid_search_service.search_lexical("PRJ-011") == []


# ==============================================================================
# 4. Empirical Evaluation Benchmark Test
# ==============================================================================


def test_empirical_evaluation_demonstrates_hybrid_superiority() -> None:
    """Verify empirical benchmark demonstrates hybrid retrieval superiority over semantic-only.

    Asserts that hybrid retrieval:
    - Achieves >= Hit@1 than semantic-only
    - Achieves >= MRR than semantic-only
    - Achieves >= Recall@5 than semantic-only
    """
    report = run_standalone_evaluation()

    sem_res = report.results["semantic"]
    hyb_res = report.results["hybrid"]
    lex_res = report.results["lexical"]

    assert hyb_res.hit_at_1 >= sem_res.hit_at_1, (
        f"Hybrid Hit@1 ({hyb_res.hit_at_1}) should be >= Semantic Hit@1 ({sem_res.hit_at_1})"
    )
    assert hyb_res.mrr >= sem_res.mrr, (
        f"Hybrid MRR ({hyb_res.mrr}) should be >= Semantic MRR ({sem_res.mrr})"
    )
    assert hyb_res.recall_at_5 >= sem_res.recall_at_5, (
        f"Hybrid Recall@5 ({hyb_res.recall_at_5}) should be >= Semantic Recall@5 ({sem_res.recall_at_5})"
    )

    # Hybrid should achieve perfect or near-perfect performance on this benchmark
    assert hyb_res.hit_at_1 >= 0.90
    assert hyb_res.mrr >= 0.90
    assert hyb_res.recall_at_5 >= 0.95
