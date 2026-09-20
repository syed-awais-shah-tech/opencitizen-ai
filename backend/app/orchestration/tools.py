"""Explicit, strictly validated tools for query orchestration.

Architectural Rule:
The model is NEVER given direct database access or raw SQL capabilities.
All interactions with vector storage and tabular engines must pass through
these explicit, validated, type-safe tools.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field, ValidationError

from app.analytics.schemas import AnalysisPlan, AnalyticalQueryRequest, AnalyticalResult
from app.orchestration.exceptions import (
    ToolArgumentValidationError,
    ToolNotPermittedError,
)
from app.search.dependencies import get_vector_search_service
from app.search.models import VectorSearchResult
from app.search.service import VectorSearchService
from app.services.analytics_service import AnalyticsService, analytics_service

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract contract for an explicit, validated orchestration tool."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human- and model-readable description of the tool capability."""

    @property
    @abstractmethod
    def input_schema(self) -> type[BaseModel]:
        """Pydantic schema enforcing validated input parameters."""

    @abstractmethod
    def execute(self, params: BaseModel, **kwargs: Any) -> Any:
        """Execute the validated tool operation."""

    def run(self, arguments: dict[str, Any], **kwargs: Any) -> Any:
        """Validate argument dictionary against schema and execute safely."""
        try:
            validated = self.input_schema.model_validate(arguments)
        except ValidationError as exc:
            raise ToolArgumentValidationError(
                tool_name=self.name,
                reason="Parameters failed schema validation.",
                details=exc.errors(),
            ) from exc

        return self.execute(validated, **kwargs)


# ==============================================================================
# Tool 1: Document Retrieval (Qdrant Semantic Search)
# ==============================================================================

class DocumentRetrievalInput(BaseModel):
    """Strict input schema for semantic document retrieval."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Semantic text inquiry to search against indexed municipal documents.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of relevant chunks to retrieve.",
    )
    score_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score threshold.",
    )
    filter_document_id: Optional[str] = Field(
        default=None,
        description="Optional specific document identifier filter.",
    )


class DocumentRetrievalTool(BaseTool):
    """Explicit tool for vector-based semantic retrieval over municipal documents in Qdrant."""

    def __init__(self, vector_service: VectorSearchService | None = None) -> None:
        self._vector_service = vector_service

    @property
    def vector_service(self) -> VectorSearchService:
        if self._vector_service is None:
            self._vector_service = get_vector_search_service()
        return self._vector_service

    @property
    def name(self) -> str:
        return "document_retrieval"

    @property
    def description(self) -> str:
        return (
            "Retrieve narrative policy excerpts, municipal reports, and textual evidence "
            "from indexed documents stored in Qdrant. Use for qualitative questions, "
            "policy statements, or explanatory context."
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return DocumentRetrievalInput

    def execute(self, params: BaseModel, **kwargs: Any) -> list[VectorSearchResult]:
        p: DocumentRetrievalInput = params  # type: ignore[assignment]
        logger.info(
            "Tool 'document_retrieval' executing query='%s' (top_k=%d, threshold=%.2f)",
            p.query,
            p.top_k,
            p.score_threshold,
        )
        return self.vector_service.search(
            query=p.query,
            top_k=p.top_k,
            score_threshold=p.score_threshold,
            filter_document_id=p.filter_document_id,
        )


# ==============================================================================
# Tool 2: Structured Data Analysis (Controlled DuckDB Pipeline)
# ==============================================================================

class DataAnalysisInput(BaseModel):
    """Strict input schema for structured tabular data analysis."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language question requiring tabular data calculation, sum, average, count, min, max, grouping, or sorting.",
    )
    table_name: Optional[str] = Field(
        default=None,
        description="Specific registered analytical table name, e.g., 'dept_expenses', 'vendor_contracts', 'regional_unemployment'.",
    )
    plan: Optional[AnalysisPlan] = Field(
        default=None,
        description="Explicit AnalysisPlan intermediate representation if pre-constructed.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Row limit for the analytical result.",
    )


class DataAnalysisTool(BaseTool):
    """Explicit tool for verified analytical calculations over structured datasets in DuckDB.
    
    CRITICAL SECURITY INVARIANT:
    Raw arbitrary SQL is never accepted from the caller or model.
    Execution strictly flows through:
    question -> intent/analysis plan -> validated SQL -> DuckDB -> structured result.
    """

    def __init__(self, service: AnalyticsService | None = None) -> None:
        self.service = service or analytics_service

    @property
    def name(self) -> str:
        return "data_analysis"

    @property
    def description(self) -> str:
        return (
            "Execute verified mathematical calculations, aggregations (count, sum, average, min, max), "
            "groupings, or sorting over structured tabular datasets in DuckDB. "
            "Never executes arbitrary SQL; strictly adheres to validated query plans."
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return DataAnalysisInput

    def execute(self, params: BaseModel, **kwargs: Any) -> AnalyticalResult:
        p: DataAnalysisInput = params  # type: ignore[assignment]
        db = kwargs.get("db")
        logger.info(
            "Tool 'data_analysis' executing for question='%s' (table=%s)",
            p.question,
            p.table_name,
        )
        request = AnalyticalQueryRequest(
            question=p.question,
            table_name=p.table_name,
            plan=p.plan,
            limit=p.limit,
        )
        return self.service.run_analytical_query(request, db=db)


# ==============================================================================
# Tool Registry & Permissions Enforcement
# ==============================================================================

class ToolRegistry:
    """Registry maintaining approved tools and strictly rejecting unapproved tool invocations."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        # Register the two permitted tools
        self.register(DocumentRetrievalTool())
        self.register(DataAnalysisTool())

    def register(self, tool: BaseTool) -> None:
        """Register an approved tool."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Lookup tool by name; raise ToolNotPermittedError if not permitted."""
        if name not in self._tools:
            raise ToolNotPermittedError(
                tool_name=name,
                allowed_tools=list(self._tools.keys()),
            )
        return self._tools[name]

    def execute(self, name: str, arguments: dict[str, Any], **kwargs: Any) -> Any:
        """Execute a permitted tool with schema validation."""
        tool = self.get_tool(name)
        return tool.run(arguments, **kwargs)

    @property
    def allowed_tool_names(self) -> list[str]:
        return list(self._tools.keys())


# Global singleton registry
tool_registry = ToolRegistry()
