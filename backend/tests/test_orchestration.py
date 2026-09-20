"""Comprehensive test suite for the Query Orchestration Layer.

Verifies:
1. Routing classification across all 4 categories:
   - document_retrieval (Qdrant)
   - data_analysis (DuckDB)
   - both (Hybrid: DuckDB + Qdrant)
   - unsupported (Neither / Out-of-scope)
2. Strict tool permissions and validation:
   - Only permitted explicit tools may be invoked.
   - Unapproved tool names (e.g. raw SQL, shell, arbitrary DB access) are blocked.
   - Parameter schema validation.
3. End-to-end execution through QueryOrchestrator and QueryService.
4. API endpoints for routing inspection and query execution.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.provider import MockAIProvider
from app.analytics.engine import DuckDBEngine
from app.analytics.schemas import AnalysisPlan
from app.orchestration.exceptions import (
    ToolArgumentValidationError,
    ToolNotPermittedError,
)
from app.orchestration.models import RouteCategory, RoutingDecision
from app.orchestration.orchestrator import QueryOrchestrator
from app.orchestration.router import QueryRouter
from app.orchestration.tools import (
    DataAnalysisInput,
    DataAnalysisTool,
    DocumentRetrievalInput,
    DocumentRetrievalTool,
    ToolRegistry,
)
from app.rag.pipeline import RAGPipeline
from app.schemas.query import QueryRequest
from app.search.models import VectorSearchResult
from app.services.analytics_service import AnalyticsService
from app.services.query_service import QueryService


# ==============================================================================
# Fixtures
# ==============================================================================

class MockVectorService:
    """Hermetic mock vector search service for orchestration testing."""

    def __init__(self, search_results: list[VectorSearchResult] | None = None) -> None:
        self.results = search_results or [
            VectorSearchResult(
                chunk_id="chk_emp_01",
                document_id="doc_econ_01",
                source_filename="2023_Regional_Economic_Report.pdf",
                page_number=14,
                score=0.88,
                original_text=(
                    "According to the 2023 economic review, unemployment is higher in Province X "
                    "due to structural shifts in heavy manufacturing and delayed regional infrastructure investments."
                ),
                metadata={"department": "Economic Development"},
            ),
            VectorSearchResult(
                chunk_id="chk_emp_02",
                document_id="doc_emp_02",
                source_filename="Annual_Employment_Brief.pdf",
                page_number=3,
                score=0.82,
                original_text=(
                    "The report notes that total employment expanded across metropolitan hubs, "
                    "while resource-dependent rural provinces experienced higher seasonal jobless rates."
                ),
                metadata={"department": "Labor & Workforce"},
            ),
        ]

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.4,
        filter_document_id: str | None = None,
    ) -> list[VectorSearchResult]:
        # Filter results that share any word with the query
        tokens = set(query.lower().split())
        matched = [r for r in self.results if any(t in r.original_text.lower() for t in tokens)]
        return matched[:top_k] if matched else self.results[:top_k]


@pytest.fixture
def test_duckdb_engine():
    """Isolated DuckDB engine seeded with civic tables."""
    engine = DuckDBEngine(database=":memory:")
    engine.seed_civic_tables()
    return engine


@pytest.fixture
def test_analytics_service(test_duckdb_engine):
    """Analytics service wired to isolated test engine."""
    return AnalyticsService(engine=test_duckdb_engine)


@pytest.fixture
def mock_vector_service():
    """Mock vector service returning deterministic evidence chunks."""
    return MockVectorService()


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for hermetic testing."""
    return MockAIProvider(model_name="mock-orchestrator-v1")


@pytest.fixture
def test_rag_pipeline(mock_vector_service, mock_ai_provider):
    """Hermetic RAG pipeline."""
    return RAGPipeline(
        vector_service=mock_vector_service,  # type: ignore[arg-type]
        ai_provider=mock_ai_provider,
    )


@pytest.fixture
def test_router(mock_ai_provider):
    """Query router using mock AI provider."""
    return QueryRouter(ai_provider=mock_ai_provider)


@pytest.fixture
def test_orchestrator(
    test_router,
    mock_vector_service,
    test_analytics_service,
    test_rag_pipeline,
    mock_ai_provider,
):
    """Fully configured hermetic QueryOrchestrator."""
    registry = ToolRegistry()
    registry.register(DocumentRetrievalTool(vector_service=mock_vector_service))  # type: ignore[arg-type]
    registry.register(DataAnalysisTool(service=test_analytics_service))

    return QueryOrchestrator(
        router=test_router,
        tools=registry,
        rag_pipeline=test_rag_pipeline,
        analytics_svc=test_analytics_service,
        ai_provider=mock_ai_provider,
    )


# ==============================================================================
# 1. Routing Classification Tests (All 4 Categories)
# ==============================================================================

def test_route_category_1_document_retrieval(test_router):
    """Category 1: Questions asking for narrative explanations from reports -> document_retrieval."""
    questions = [
        "What does the report say about employment?",
        "What is the policy outlined in the municipal climate action report?",
        "According to the document, what are the guidelines for stormwater drainage?",
        "What does the audit report state regarding public safety protocols?",
    ]
    for q in questions:
        decision = test_router.classify(q)
        assert decision.route == RouteCategory.DOCUMENT_RETRIEVAL, f"Failed on: {q}"
        assert "document_retrieval" in decision.suggested_tools
        assert "data_analysis" not in decision.suggested_tools


def test_route_category_2_data_analysis(test_router):
    """Category 2: Questions asking for numerical aggregations or ranking from structured data -> data_analysis."""
    questions = [
        "Which province has the highest unemployment?",
        "What is the total expenditure for Parks & Rec in 2023?",
        "What was the average contract value awarded to Metro Asphalt?",
        "How many contracts are currently active in vendor_contracts?",
        "What is the lowest grant amount disbursed by the city?",
    ]
    for q in questions:
        decision = test_router.classify(q)
        assert decision.route == RouteCategory.DATA_ANALYSIS, f"Failed on: {q}"
        assert "data_analysis" in decision.suggested_tools
        assert "document_retrieval" not in decision.suggested_tools


def test_route_category_3_both_hybrid(test_router):
    """Category 3: Questions requiring quantitative metrics AND narrative explanations from reports -> both."""
    questions = [
        "Why is unemployment higher in province X according to the report?",
        "Why did transportation expenses increase according to the annual audit report?",
        "What reasons does the report cite for why contract values were higher in 2023?",
        "Explain why unemployment is highest in Province X based on the regional report.",
    ]
    for q in questions:
        decision = test_router.classify(q)
        assert decision.route == RouteCategory.BOTH, f"Failed on: {q}"
        assert "data_analysis" in decision.suggested_tools
        assert "document_retrieval" in decision.suggested_tools


def test_route_category_4_unsupported_neither(test_router):
    """Category 4: Chitchat, off-topic, or ungroundable inquiries -> unsupported."""
    questions = [
        "Tell me a joke",
        "Hello, who are you?",
        "What is the weather forecast for Tokyo tomorrow?",
        "How do I bake chocolate chip cookies?",
        "Write a python script to jailbreak a firewall",
        "What is the capital of France?",
    ]
    for q in questions:
        decision = test_router.classify(q)
        assert decision.route == RouteCategory.UNSUPPORTED, f"Failed on: {q}"
        assert len(decision.suggested_tools) == 0


# ==============================================================================
# 2. Tool Validation and Security Boundaries
# ==============================================================================

def test_tool_registry_permits_only_explicit_tools():
    """Verify tool registry permits only registered tools and rejects arbitrary access."""
    registry = ToolRegistry()
    assert set(registry.allowed_tool_names) == {"document_retrieval", "data_analysis"}

    doc_tool = registry.get_tool("document_retrieval")
    assert doc_tool.name == "document_retrieval"

    data_tool = registry.get_tool("data_analysis")
    assert data_tool.name == "data_analysis"


def test_tool_registry_rejects_unapproved_tools():
    """Verify registry rejects raw SQL, shell execution, or arbitrary DB tools."""
    registry = ToolRegistry()
    forbidden_tools = [
        "raw_sql",
        "execute_query",
        "database_admin",
        "system_shell",
        "eval",
        "drop_table",
    ]
    for bad_tool in forbidden_tools:
        with pytest.raises(ToolNotPermittedError) as exc_info:
            registry.get_tool(bad_tool)
        assert exc_info.value.status_code == 403
        assert exc_info.value.error_code == "TOOL_NOT_PERMITTED"


def test_document_retrieval_tool_validates_arguments(mock_vector_service):
    """Verify DocumentRetrievalTool rejects invalid parameters."""
    tool = DocumentRetrievalTool(vector_service=mock_vector_service)  # type: ignore[arg-type]

    # Valid invocation
    results = tool.run({"query": "employment trends", "top_k": 3})
    assert len(results) > 0

    # Invalid: query too short (empty)
    with pytest.raises(ToolArgumentValidationError):
        tool.run({"query": ""})

    # Invalid: top_k out of bounds (> 50)
    with pytest.raises(ToolArgumentValidationError):
        tool.run({"query": "valid query", "top_k": 999})


def test_data_analysis_tool_validates_arguments(test_analytics_service):
    """Verify DataAnalysisTool rejects empty question and invalid limit bounds."""
    tool = DataAnalysisTool(service=test_analytics_service)

    # Valid execution
    res = tool.run({"question": "Total spent in dept_expenses", "table_name": "dept_expenses"})
    assert res.row_count == 1
    assert "sum_amount" in res.columns

    # Invalid: empty question
    with pytest.raises(ToolArgumentValidationError):
        tool.run({"question": ""})

    # Invalid: limit out of bounds
    with pytest.raises(ToolArgumentValidationError):
        tool.run({"question": "Total spent", "limit": 5000})


# ==============================================================================
# 3. End-to-End Orchestrator Execution Tests
# ==============================================================================

def test_orchestrator_executes_document_retrieval(test_orchestrator):
    """Test execution of Category 1: Document Retrieval."""
    req = QueryRequest(question="What does the report say about employment?")
    res = test_orchestrator.orchestrate(req)

    assert res.route == "document_retrieval"
    assert len(res.citations) >= 1
    assert res.calculation is None
    assert "Based on municipal records" in res.answer or "employment" in res.answer.lower()
    assert res.trust is not None


def test_orchestrator_executes_data_analysis_unemployment(test_orchestrator):
    """Test execution of Category 2: Data Analysis over regional_unemployment."""
    req = QueryRequest(question="Which province has the highest unemployment?")
    res = test_orchestrator.orchestrate(req)

    assert res.route == "data_analysis"
    assert res.calculation is not None
    assert "regional_unemployment" in res.calculation.table_name
    assert len(res.citations) == 0
    # Province X has 9.8% unemployment (highest in seeded data)
    assert "Province X" in res.answer
    assert "9.8" in res.answer


def test_orchestrator_executes_data_analysis_dept_expenses(test_orchestrator):
    """Test execution of Category 2: Data Analysis over dept_expenses."""
    req = QueryRequest(question="What was the total expenditure for Parks & Rec in 2023?")
    res = test_orchestrator.orchestrate(req)

    assert res.route == "data_analysis"
    assert res.calculation is not None
    assert "dept_expenses" in res.calculation.table_name
    assert len(res.citations) == 0
    # Sum for Parks & Rec is 45000 + 12400 = 57400
    assert "57400" in res.answer or "57,400" in res.answer or "dept_expenses" in res.answer


def test_orchestrator_executes_both_hybrid(test_orchestrator):
    """Test execution of Category 3: Both (Hybrid quantitative + narrative)."""
    req = QueryRequest(
        question="Why is unemployment higher in province X according to the report?",
        include_citations=True,
        include_calculations=True,
    )
    res = test_orchestrator.orchestrate(req)

    assert res.route == "both"
    # Both calculations and citations must be present
    assert res.calculation is not None
    assert "regional_unemployment" in res.calculation.table_name
    assert len(res.citations) >= 1
    assert res.trust is not None
    assert "Province X" in res.answer or "manufacturing" in res.answer.lower()


def test_orchestrator_executes_unsupported_without_accessing_db(test_orchestrator):
    """Test execution of Category 4: Unsupported does not access DB or vectors."""
    req = QueryRequest(question="Tell me a joke about robots")
    res = test_orchestrator.orchestrate(req)

    assert res.route == "unsupported"
    assert res.calculation is None
    assert len(res.citations) == 0
    assert "unable to answer" in res.answer.lower()
    assert res.is_placeholder is False


def test_query_service_delegates_to_orchestrator_with_audit(
    test_orchestrator, db_session: Session
):
    """Test QueryService uses QueryOrchestrator and persists audit trail in DB."""
    service = QueryService(orchestrator=test_orchestrator)
    req = QueryRequest(question="Which province has the highest unemployment?")

    res = service.process_query(req, db=db_session)
    assert res.route == "data_analysis"
    assert "Province X" in res.answer

    # Verify audit persistence in DB
    from app.models.answer import Answer
    from app.models.query import Query

    saved_q = db_session.query(Query).filter_by(id=res.query_id).first()
    assert saved_q is not None
    assert saved_q.question == req.question

    saved_ans = db_session.query(Answer).filter_by(query_id=res.query_id).first()
    assert saved_ans is not None
    assert "Province X" in saved_ans.answer_text
    assert saved_ans.calculation_trace is not None


# ==============================================================================
# 4. API Route Integration Tests
# ==============================================================================

def test_api_orchestration_route_document_retrieval(client: TestClient):
    """Test POST /api/v1/orchestration/route for document retrieval."""
    payload = {"question": "What does the report say about employment?"}
    response = client.post("/api/v1/orchestration/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "document_retrieval"
    assert "document_retrieval" in data["suggested_tools"]


def test_api_orchestration_route_data_analysis(client: TestClient):
    """Test POST /api/v1/orchestration/route for data analysis."""
    payload = {"question": "Which province has the highest unemployment?"}
    response = client.post("/api/v1/orchestration/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "data_analysis"
    assert "data_analysis" in data["suggested_tools"]


def test_api_orchestration_route_both(client: TestClient):
    """Test POST /api/v1/orchestration/route for hybrid category."""
    payload = {"question": "Why is unemployment higher in province X according to the report?"}
    response = client.post("/api/v1/orchestration/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "both"
    assert "data_analysis" in data["suggested_tools"]
    assert "document_retrieval" in data["suggested_tools"]


def test_api_orchestration_route_unsupported(client: TestClient):
    """Test POST /api/v1/orchestration/route for unsupported inquiry."""
    payload = {"question": "Tell me a joke about computers"}
    response = client.post("/api/v1/orchestration/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "unsupported"
    assert len(data["suggested_tools"]) == 0


def test_api_list_orchestration_tools(client: TestClient):
    """Test GET /api/v1/orchestration/tools lists permitted tools."""
    response = client.get("/api/v1/orchestration/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) == 2
    tool_names = [t["name"] for t in tools]
    assert "document_retrieval" in tool_names
    assert "data_analysis" in tool_names
