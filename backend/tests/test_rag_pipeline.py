"""Comprehensive tests for Stage 7 RAG pipeline, AI provider abstraction, and citation grounding."""

import pytest
from app.ai.models import EvidenceContext, LLMAnswer
from app.ai.prompts import (
    INSUFFICIENT_EVIDENCE_PHRASE,
    OPENCITIZEN_SYSTEM_INSTRUCTION,
    build_rag_prompt,
)
from app.ai.provider import (
    BaseAIProvider,
    GeminiProvider,
    MockAIProvider,
)
from app.ingestion.models import DocumentChunk
from app.models.base import Base
from app.rag.models import RAGResponse
from app.rag.pipeline import RAGPipeline
from app.schemas.query import QueryRequest
from app.search.embeddings import DeterministicEmbeddingProvider
from app.search.service import VectorSearchService
from app.search.vector_store import QdrantVectorStore
from app.services.query_service import QueryService
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def in_memory_qdrant() -> QdrantClient:
    """Provide isolated in-memory Qdrant instance for test execution."""
    return QdrantClient(location=":memory:")


@pytest.fixture
def embedding_provider() -> DeterministicEmbeddingProvider:
    """Provide deterministic embedding generator with 64 dimensions for tests."""
    return DeterministicEmbeddingProvider(dimension=64, model_name="test-64d")


@pytest.fixture
def vector_service(
    in_memory_qdrant: QdrantClient,
    embedding_provider: DeterministicEmbeddingProvider,
) -> VectorSearchService:
    """Provide VectorSearchService wired with in-memory Qdrant and deterministic embeddings."""
    store = QdrantVectorStore(
        client=in_memory_qdrant,
        default_collection="test_rag_collection",
        dimension=embedding_provider.dimension,
    )
    return VectorSearchService(
        vector_store=store,
        embedding_provider=embedding_provider,
        collection_name="test_rag_collection",
    )


@pytest.fixture
def mock_ai_provider() -> MockAIProvider:
    """Provide deterministic MockAIProvider for grounding and citation tests."""
    return MockAIProvider(model_name="mock-test-llm")


@pytest.fixture
def rag_pipeline(
    vector_service: VectorSearchService,
    mock_ai_provider: MockAIProvider,
) -> RAGPipeline:
    """Provide RAGPipeline wired with in-memory vector store and mock AI provider."""
    return RAGPipeline(
        vector_service=vector_service,
        ai_provider=mock_ai_provider,
        top_k=3,
        score_threshold=0.01,
    )


@pytest.fixture
def seeded_rag_pipeline(
    rag_pipeline: RAGPipeline,
    vector_service: VectorSearchService,
) -> RAGPipeline:
    """Provide RAGPipeline seeded with representative municipal chunks."""
    chunks = [
        DocumentChunk(
            chunk_id="chk_library_p3_01",
            document_id="doc-annual-budget-2024",
            source_filename="City_Budget_2024.pdf",
            page_number=3,
            chunk_index=0,
            text="The municipal allocation for public libraries and community reading programs in fiscal year 2024 is 8.5 million dollars.",
            character_count=123,
            word_count=18,
            metadata={"department": "Public Libraries", "fiscal_year": 2024},
        ),
        DocumentChunk(
            chunk_id="chk_transit_p7_02",
            document_id="doc-transit-masterplan",
            source_filename="Transit_Masterplan_2024.pdf",
            page_number=7,
            chunk_index=1,
            text="Transit line expansion added twelve electric buses to the downtown transit corridor.",
            character_count=88,
            word_count=12,
            metadata={"department": "Transportation", "status": "approved"},
        ),
    ]
    vector_service.index_chunks(chunks)
    return rag_pipeline


@pytest.fixture
def db_session() -> Session:
    """Provide an in-memory SQLite database session for auditing tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# ==============================================================================
# 1. Test for Successful Retrieval
# ==============================================================================


def test_rag_successful_retrieval(
    seeded_rag_pipeline: RAGPipeline,
) -> None:
    """Test question flow: question -> processing -> vector retrieval -> relevant chunks -> AI -> answer."""
    question = (
        "What is the municipal allocation for public libraries in fiscal year 2024?"
    )
    response: RAGResponse = seeded_rag_pipeline.run(question)

    assert response.is_insufficient_evidence is False
    assert response.retrieved_chunks_count >= 1
    assert "8.5 million dollars" in response.answer
    assert response.latency_ms >= 0.0
    assert response.model_name == "mock-test-llm"


# ==============================================================================
# 2. Test for No Retrieval Results
# ==============================================================================


def test_rag_no_retrieval_results_empty_store(
    rag_pipeline: RAGPipeline,
) -> None:
    """Test that querying an empty vector collection returns insufficient evidence with zero citations."""
    question = "What was the total expenditure for parks and recreation?"
    response: RAGResponse = rag_pipeline.run(question)

    assert response.is_insufficient_evidence is True
    assert response.retrieved_chunks_count == 0
    assert response.citations == []
    assert response.answer == INSUFFICIENT_EVIDENCE_PHRASE


def test_rag_no_retrieval_results_unmatched_query(
    seeded_rag_pipeline: RAGPipeline,
) -> None:
    """Test that querying with unattainable score threshold returns insufficient evidence."""
    question = "What is the allocation for deep space telescopes?"
    response: RAGResponse = seeded_rag_pipeline.run(question, score_threshold=0.9999)

    assert response.is_insufficient_evidence is True
    assert response.citations == []
    assert response.answer == INSUFFICIENT_EVIDENCE_PHRASE


# ==============================================================================
# 3. Test for Answer with Citations & Metadata Preservation
# ==============================================================================


def test_rag_answer_with_citations_and_metadata_preservation(
    seeded_rag_pipeline: RAGPipeline,
) -> None:
    """Test that grounded answer includes inline source references and preserves metadata."""
    question = "How many electric buses were added to the downtown corridor in the transit line expansion?"
    response: RAGResponse = seeded_rag_pipeline.run(question)

    assert response.is_insufficient_evidence is False
    assert len(response.citations) >= 1

    # Verify inline reference in answer text
    assert "[Source: Transit_Masterplan_2024.pdf, Page: 7]" in response.answer

    # Verify structured citations preserve all required metadata
    transit_cit = next(
        c
        for c in response.citations
        if c.document_title == "Transit_Masterplan_2024.pdf"
    )
    assert transit_cit.document_title == "Transit_Masterplan_2024.pdf"
    assert transit_cit.page_number == 7
    assert transit_cit.chunk_id == "chk_transit_p7_02"
    assert "twelve electric buses" in transit_cit.excerpt
    assert transit_cit.similarity_score > 0.0
    assert transit_cit.department == "Transportation"


def test_no_fabricated_citations(
    seeded_rag_pipeline: RAGPipeline,
) -> None:
    """Ensure pipeline never invents or fabricates citations not present in retrieved evidence."""
    question = "What was the library allocation in 2024?"
    response: RAGResponse = seeded_rag_pipeline.run(question)

    valid_filenames = {"City_Budget_2024.pdf", "Transit_Masterplan_2024.pdf"}
    for cit in response.citations:
        assert cit.document_title in valid_filenames
        assert cit.page_number in (3, 7)
        assert cit.excerpt != ""


# ==============================================================================
# 4. Test for Insufficient Evidence
# ==============================================================================


def test_rag_insufficient_evidence_when_chunks_unrelated(
    seeded_rag_pipeline: RAGPipeline,
) -> None:
    """Test that when retrieved chunks lack information to answer the question,

    the system explicitly outputs the standard insufficient evidence statement.
    """
    # Seeded chunks only discuss libraries and electric buses
    irrelevant_question = (
        "What is the average salary of orbital astronauts on lunar stations?"
    )
    response: RAGResponse = seeded_rag_pipeline.run(
        irrelevant_question, score_threshold=0.0
    )

    assert response.is_insufficient_evidence is True
    assert response.answer == INSUFFICIENT_EVIDENCE_PHRASE
    assert response.citations == []


# ==============================================================================
# 5. Test AI Service Abstraction & Swappability
# ==============================================================================


def test_custom_ai_provider_swappability(
    vector_service: VectorSearchService,
) -> None:
    """Test that custom AI providers can be swapped into RAG pipeline without code changes."""

    class CustomGroundedProvider(BaseAIProvider):
        @property
        def model_name(self) -> str:
            return "custom-grounded-test-v1"

        def generate_grounded_answer(
            self, question: str, contexts: list[EvidenceContext]
        ) -> LLMAnswer:
            return LLMAnswer(
                answer_text=f"Custom grounded response for '{question}' using {len(contexts)} sources.",
                is_grounded=True,
                is_insufficient_evidence=False,
                model_name=self.model_name,
                citation_references=[c.document_title for c in contexts],
            )

        def generate_text(
            self, prompt: str, system_instruction: str | None = None
        ) -> str:
            return "Custom raw text."

    custom_provider = CustomGroundedProvider()
    custom_pipeline = RAGPipeline(
        vector_service=vector_service,
        ai_provider=custom_provider,
        score_threshold=None,
    )

    # Seed one chunk
    vector_service.index_chunks(
        [
            DocumentChunk(
                chunk_id="chk_test_01",
                document_id="doc_01",
                source_filename="sample.pdf",
                page_number=1,
                chunk_index=0,
                text="Sample municipal record text.",
                character_count=30,
                word_count=4,
            )
        ]
    )

    response = custom_pipeline.run("Sample municipal record")
    assert response.is_insufficient_evidence is False
    assert response.model_name == "custom-grounded-test-v1"
    assert "Custom grounded response" in response.answer
    assert len(response.citations) == 1


def test_gemini_provider_init_validation() -> None:
    """Test GeminiProvider initializes with key or raises ValueError if missing."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        GeminiProvider(api_key="")

    # When key is provided, initializes properly
    provider = GeminiProvider(
        api_key="mock_test_key_for_init", model="gemini-1.5-flash"
    )
    assert provider.model_name == "gemini-1.5-flash"


def test_system_prompt_grounding_rules() -> None:
    """Verify system prompt contains critical grounding rules and insufficient evidence instruction."""
    assert "CRITICAL GROUNDING RULES" in OPENCITIZEN_SYSTEM_INSTRUCTION
    assert INSUFFICIENT_EVIDENCE_PHRASE in OPENCITIZEN_SYSTEM_INSTRUCTION
    assert "NEVER fabricate" in OPENCITIZEN_SYSTEM_INSTRUCTION


def test_build_rag_prompt_structure() -> None:
    """Verify build_rag_prompt constructs formatted evidence sections."""
    contexts = [
        EvidenceContext(
            document_title="Report.pdf",
            page_number=2,
            chunk_id="chk_rep_01",
            text="Operating expenses totaled 200,000.",
            score=0.9,
        )
    ]
    prompt = build_rag_prompt("What were operating expenses?", contexts)
    assert "--- EVIDENCE EXCERPT [1] ---" in prompt
    assert "Source File: Report.pdf" in prompt
    assert "Page Number: 2" in prompt
    assert "Chunk ID: chk_rep_01" in prompt
    assert "USER QUESTION:" in prompt


# ==============================================================================
# 6. Test QueryService End-to-End Persistence
# ==============================================================================


def test_query_service_with_rag_and_db_audit(
    seeded_rag_pipeline: RAGPipeline,
    db_session: Session,
) -> None:
    """Test QueryService processes request via RAG pipeline and persists Query, Answer, Citation."""
    svc = QueryService(rag_pipeline=seeded_rag_pipeline)

    request = QueryRequest(
        question="What was the allocation for public libraries in fiscal year 2024?",
        include_citations=True,
    )

    response = svc.process_query(request, db=db_session)

    assert response.question == request.question
    assert "8.5 million dollars" in response.answer
    assert len(response.citations) >= 1
    assert response.status == "completed"

    # Verify audit trail committed in database
    from app.models.answer import Answer
    from app.models.citation import Citation
    from app.models.query import Query

    db_query = db_session.query(Query).filter_by(id=response.query_id).first()
    assert db_query is not None
    assert db_query.question == request.question

    db_answer = db_session.query(Answer).filter_by(query_id=response.query_id).first()
    assert db_answer is not None
    assert "8.5 million dollars" in db_answer.answer_text

    db_citations = db_session.query(Citation).filter_by(answer_id=db_answer.id).all()
    assert len(db_citations) >= 1
    assert db_citations[0].document_title == "City_Budget_2024.pdf"
    assert db_citations[0].page_number == 3
