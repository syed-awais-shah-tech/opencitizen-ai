"""Comprehensive tests for Stage 6 Vector Search Service, Qdrant integration, and Embedding providers."""

import pytest
from app.ingestion.models import DocumentChunk
from app.search.embeddings import (
    BaseEmbeddingProvider,
    DeterministicEmbeddingProvider,
    get_embedding_provider,
)
from app.search.models import VectorIndexResult, VectorSearchResult
from app.search.service import VectorSearchService
from app.search.vector_store import QdrantVectorStore, chunk_id_to_point_id
from qdrant_client import QdrantClient


@pytest.fixture
def in_memory_qdrant_client() -> QdrantClient:
    """Fixture providing a fresh isolated in-memory Qdrant instance."""
    return QdrantClient(location=":memory:")


@pytest.fixture
def embedding_provider() -> DeterministicEmbeddingProvider:
    """Fixture providing deterministic embedding generator with 64 dimensions for tests."""
    return DeterministicEmbeddingProvider(
        dimension=64, model_name="test-deterministic-64"
    )


@pytest.fixture
def qdrant_vector_store(
    in_memory_qdrant_client: QdrantClient,
    embedding_provider: DeterministicEmbeddingProvider,
) -> QdrantVectorStore:
    """Fixture providing QdrantVectorStore backed by in-memory Qdrant."""
    return QdrantVectorStore(
        client=in_memory_qdrant_client,
        default_collection="test_opencitizen_documents",
        dimension=embedding_provider.dimension,
    )


@pytest.fixture
def vector_search_service(
    qdrant_vector_store: QdrantVectorStore,
    embedding_provider: DeterministicEmbeddingProvider,
) -> VectorSearchService:
    """Fixture providing VectorSearchService wired with in-memory store and deterministic provider."""
    return VectorSearchService(
        vector_store=qdrant_vector_store,
        embedding_provider=embedding_provider,
        collection_name="test_opencitizen_documents",
    )


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    """Fixture providing diverse document chunks for indexing and retrieval verification."""
    return [
        DocumentChunk(
            chunk_id="chk_docA_p1_0",
            document_id="doc-audit-2024",
            source_filename="city_budget_audit_2024.pdf",
            page_number=1,
            chunk_index=0,
            text="The municipal audit revealed 12 million dollars allocated to public park maintenance.",
            character_count=85,
            word_count=12,
            metadata={"fiscal_year": 2024, "department": "Parks & Recreation"},
        ),
        DocumentChunk(
            chunk_id="chk_docA_p2_1",
            document_id="doc-audit-2024",
            source_filename="city_budget_audit_2024.pdf",
            page_number=2,
            chunk_index=1,
            text="Highway maintenance received 45 million dollars for emergency pothole and bridge repairs.",
            character_count=90,
            word_count=12,
            metadata={"fiscal_year": 2024, "department": "Transportation"},
        ),
        DocumentChunk(
            chunk_id="chk_docB_p5_0",
            document_id="doc-health-2024",
            source_filename="public_health_notice.pdf",
            page_number=5,
            chunk_index=0,
            text="Community healthcare centers will provide free pediatric wellness examinations and immunizations.",
            character_count=99,
            word_count=11,
            metadata={"category": "Healthcare", "confidential": False},
        ),
        DocumentChunk(
            chunk_id="chk_docB_p6_1",
            document_id="doc-health-2024",
            source_filename="public_health_notice.pdf",
            page_number=6,
            chunk_index=1,
            text="Water quality inspections confirmed municipal drinking water complies with all federal purity standards.",
            character_count=107,
            word_count=13,
            metadata={
                "category": "Environmental Health",
                "target_region": "North District",
            },
        ),
    ]


# ==============================================================================
# 1. Tests for Indexing
# ==============================================================================


def test_indexing_single_chunk(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test indexing a single chunk successfully registers point and collection."""
    single_chunk = sample_chunks[:1]
    result: VectorIndexResult = vector_search_service.index_chunks(single_chunk)

    assert result.indexed_count == 1
    assert result.collection_name == "test_opencitizen_documents"
    assert result.document_ids == ["doc-audit-2024"]
    assert result.duration_ms >= 0.0
    assert vector_search_service.count() == 1


def test_indexing_multiple_chunks_batch(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test indexing multiple chunks across different documents in a single batch."""
    result: VectorIndexResult = vector_search_service.index_chunks(sample_chunks)

    assert result.indexed_count == 4
    assert set(result.document_ids) == {"doc-audit-2024", "doc-health-2024"}
    assert vector_search_service.count() == 4


def test_indexing_empty_list_returns_zero(
    vector_search_service: VectorSearchService,
) -> None:
    """Test indexing empty sequence of chunks returns 0 without errors."""
    result: VectorIndexResult = vector_search_service.index_chunks([])

    assert result.indexed_count == 0
    assert result.document_ids == []
    assert vector_search_service.count() == 0


def test_indexing_idempotence_upsert(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test that indexing the same chunks twice updates points rather than duplicating."""
    vector_search_service.index_chunks(sample_chunks)
    assert vector_search_service.count() == 4

    # Index same chunks again
    res2 = vector_search_service.index_chunks(sample_chunks)
    assert res2.indexed_count == 4
    # Total count remains 4 because IDs match
    assert vector_search_service.count() == 4


def test_vector_store_mismatched_vectors_raises(
    qdrant_vector_store: QdrantVectorStore,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test that base vector store rejects mismatched chunk and vector counts."""
    mismatched_vectors = [[0.1] * 64]  # only 1 vector for 4 chunks
    with pytest.raises(ValueError, match="Chunks count .* must match vectors count"):
        qdrant_vector_store.index_chunks(sample_chunks, mismatched_vectors)


# ==============================================================================
# 2. Tests for Retrieval & Semantic Search
# ==============================================================================


def test_semantic_retrieval_top_k_limit(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test retrieval respects the top_k parameter."""
    vector_search_service.index_chunks(sample_chunks)

    # Search with top_k=2
    results = vector_search_service.search("municipal expenditure and repairs", top_k=2)

    assert len(results) == 2
    assert all(isinstance(r, VectorSearchResult) for r in results)
    # Ensure results are sorted descending by score
    assert results[0].score >= results[1].score


def test_semantic_retrieval_ranking_relevance(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test that semantic query returns the most relevant chunk as top result."""
    vector_search_service.index_chunks(sample_chunks)

    # Query specifically matching healthcare and immunizations
    health_results = vector_search_service.search(
        "free pediatric immunizations healthcare", top_k=1
    )
    assert len(health_results) == 1
    top_hit = health_results[0]
    assert top_hit.chunk_id == "chk_docB_p5_0"
    assert top_hit.document_id == "doc-health-2024"
    assert "immunizations" in top_hit.original_text

    # Query specifically matching highway repairs
    highway_results = vector_search_service.search(
        "highway bridge pothole repairs", top_k=1
    )
    assert len(highway_results) == 1
    assert highway_results[0].chunk_id == "chk_docA_p2_1"
    assert "pothole" in highway_results[0].original_text


def test_retrieval_with_document_id_filter(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test searching with document_id filter isolates results to specified document."""
    vector_search_service.index_chunks(sample_chunks)

    # General query that could match anything, but restricted to doc-audit-2024
    results = vector_search_service.search(
        query="maintenance and repairs",
        top_k=5,
        filter_document_id="doc-audit-2024",
    )

    assert len(results) > 0
    for r in results:
        assert r.document_id == "doc-audit-2024"
        assert r.document_id != "doc-health-2024"


def test_retrieval_score_threshold_filter(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test that results below score_threshold are filtered out."""
    vector_search_service.index_chunks(sample_chunks)

    # First get unconstrained search to inspect score
    all_hits = vector_search_service.search("drinking water purity standards", top_k=4)
    assert len(all_hits) > 0
    top_score = all_hits[0].score

    # Setting threshold slightly below top score returns only relevant hits
    filtered_hits = vector_search_service.search(
        "drinking water purity standards",
        top_k=4,
        score_threshold=top_score - 0.05,
    )
    assert len(filtered_hits) >= 1
    assert all(h.score >= (top_score - 0.05) for h in filtered_hits)


# ==============================================================================
# 3. Tests for Empty Results
# ==============================================================================


def test_search_empty_collection_returns_empty_list(
    vector_search_service: VectorSearchService,
) -> None:
    """Test searching an empty collection returns an empty list without error."""
    results = vector_search_service.search("any query", top_k=5)
    assert results == []


def test_search_empty_or_whitespace_query_returns_empty_list(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test searching with blank or whitespace-only query string returns empty list."""
    vector_search_service.index_chunks(sample_chunks)

    assert vector_search_service.search("") == []
    assert vector_search_service.search("   ") == []
    assert vector_search_service.search("\n\t") == []


def test_search_unmatched_document_id_filter_returns_empty_list(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test searching with non-existent document_id returns empty list."""
    vector_search_service.index_chunks(sample_chunks)

    results = vector_search_service.search(
        "municipal public park maintenance",
        top_k=5,
        filter_document_id="non-existent-document-xyz",
    )
    assert results == []


def test_search_unattainable_score_threshold_returns_empty_list(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test searching with unattainable similarity threshold returns empty list."""
    vector_search_service.index_chunks(sample_chunks)

    # Impossible cosine similarity > 1.0
    results = vector_search_service.search(
        "pediatric immunizations", top_k=5, score_threshold=1.0001
    )
    assert results == []


# ==============================================================================
# 4. Tests for Metadata Preservation
# ==============================================================================


def test_metadata_preservation_all_required_fields(
    vector_search_service: VectorSearchService,
) -> None:
    """Test that all 5 required metadata fields (doc ID, chunk ID, page number,

    source filename, original text) and extra metadata are fully preserved.
    """
    target_chunk = DocumentChunk(
        chunk_id="chk_prov_doc_999_p4_2",
        document_id="prov-doc-999",
        source_filename="environmental_assessment_final.pdf",
        page_number=4,
        chunk_index=2,
        text="Wetland biodiversity surveys recorded twenty distinct bird species in the conservation zone.",
        character_count=94,
        word_count=13,
        metadata={
            "survey_year": 2024,
            "lead_ecologist": "Dr. Aris Thorne",
            "zone_code": "WZ-04",
        },
    )

    # Index chunk
    vector_search_service.index_chunks([target_chunk])

    # Search specifically for wetland biodiversity
    results = vector_search_service.search(
        "wetland biodiversity conservation zone", top_k=1
    )
    assert len(results) == 1

    match = results[0]

    # Explicitly verify the 5 mandatory metadata fields required by specification:
    # 1. document ID
    assert match.document_id == "prov-doc-999"
    # 2. chunk ID
    assert match.chunk_id == "chk_prov_doc_999_p4_2"
    # 3. page number
    assert match.page_number == 4
    # 4. source filename
    assert match.source_filename == "environmental_assessment_final.pdf"
    # 5. original text
    assert (
        match.original_text
        == "Wetland biodiversity surveys recorded twenty distinct bird species in the conservation zone."
    )

    # In addition, check extra payload metadata preservation
    assert match.metadata["survey_year"] == 2024
    assert match.metadata["lead_ecologist"] == "Dr. Aris Thorne"
    assert match.metadata["zone_code"] == "WZ-04"
    assert match.score > 0.0


# ==============================================================================
# 5. Tests for Provider Abstraction Swappability & Document Deletion
# ==============================================================================


def test_custom_mock_embedding_provider_swappability(
    in_memory_qdrant_client: QdrantClient,
) -> None:
    """Test that a different custom embedding provider can be plugged in seamlessly

    without modifying or coupling to QdrantVectorStore.
    """

    class AlternateMockProvider(BaseEmbeddingProvider):
        @property
        def dimension(self) -> int:
            return 8

        @property
        def model_name(self) -> str:
            return "alternate-test-8d"

        def embed_text(self, text: str) -> list[float]:
            # Simple constant normalized 8-d vector
            v = [1.0 / (8**0.5)] * 8
            return v

        def embed_batch(self, texts: list[str]) -> list[list[float]]:
            return [self.embed_text(t) for t in texts]

    alt_provider = AlternateMockProvider()
    alt_store = QdrantVectorStore(
        client=in_memory_qdrant_client,
        default_collection="alternate_collection",
        dimension=alt_provider.dimension,
    )
    alt_service = VectorSearchService(
        vector_store=alt_store,
        embedding_provider=alt_provider,
        collection_name="alternate_collection",
    )

    test_chunk = DocumentChunk(
        chunk_id="chk_alt_001",
        document_id="doc-alt",
        source_filename="test.pdf",
        page_number=1,
        chunk_index=0,
        text="Test chunk for alternative embedding provider.",
        character_count=45,
        word_count=6,
    )

    index_res = alt_service.index_chunks([test_chunk])
    assert index_res.indexed_count == 1

    search_res = alt_service.search("query", top_k=1)
    assert len(search_res) == 1
    assert search_res[0].chunk_id == "chk_alt_001"
    assert (
        search_res[0].original_text == "Test chunk for alternative embedding provider."
    )


def test_delete_document_vectors(
    vector_search_service: VectorSearchService,
    sample_chunks: list[DocumentChunk],
) -> None:
    """Test deleting all vectors associated with a specific document ID."""
    vector_search_service.index_chunks(sample_chunks)
    assert vector_search_service.count() == 4

    # Delete doc-audit-2024 (2 chunks)
    deleted_count = vector_search_service.delete_document("doc-audit-2024")
    assert deleted_count == 2
    assert vector_search_service.count() == 2

    # Verify search no longer returns deleted document
    audit_results = vector_search_service.search("municipal audit park", top_k=5)
    for res in audit_results:
        assert res.document_id != "doc-audit-2024"


def test_chunk_id_to_point_id_deterministic() -> None:
    """Test chunk_id_to_point_id returns valid RFC 4122 UUID and is deterministic."""
    import uuid

    chunk_id = "chk_doc123_p1_0"
    point_id_1 = chunk_id_to_point_id(chunk_id)
    point_id_2 = chunk_id_to_point_id(chunk_id)

    assert point_id_1 == point_id_2
    # Check valid UUID
    parsed = uuid.UUID(point_id_1)
    assert str(parsed) == point_id_1

    # When already a UUID, preserves it
    random_uuid = str(uuid.uuid4())
    assert chunk_id_to_point_id(random_uuid) == random_uuid


def test_embedding_factory_deterministic_resolution() -> None:
    """Test embedding factory returns DeterministicEmbeddingProvider."""
    provider = get_embedding_provider("deterministic", dimension=128)
    assert isinstance(provider, DeterministicEmbeddingProvider)
    assert provider.dimension == 128

    with pytest.raises(ValueError, match="Unsupported embedding provider type"):
        get_embedding_provider("unsupported_provider_foo")
