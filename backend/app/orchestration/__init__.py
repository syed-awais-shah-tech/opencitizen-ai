"""Query orchestration layer for controlled routing, tool execution, and multi-source synthesis."""

from app.orchestration.exceptions import (
    OrchestrationError,
    RoutingClassificationError,
    ToolArgumentValidationError,
    ToolNotPermittedError,
)
from app.orchestration.models import (
    RouteCategory,
    RouteRequest,
    RoutingDecision,
    ToolCall,
    ToolExecutionResult,
)
from app.orchestration.orchestrator import QueryOrchestrator, query_orchestrator
from app.orchestration.router import QueryRouter, query_router_service
from app.orchestration.tools import (
    BaseTool,
    DataAnalysisInput,
    DataAnalysisTool,
    DocumentRetrievalInput,
    DocumentRetrievalTool,
    ToolRegistry,
    tool_registry,
)

__all__ = [
    "BaseTool",
    "DataAnalysisInput",
    "DataAnalysisTool",
    "DocumentRetrievalInput",
    "DocumentRetrievalTool",
    "OrchestrationError",
    "QueryOrchestrator",
    "QueryRouter",
    "RouteCategory",
    "RouteRequest",
    "RoutingClassificationError",
    "RoutingDecision",
    "ToolArgumentValidationError",
    "ToolCall",
    "ToolExecutionResult",
    "ToolNotPermittedError",
    "ToolRegistry",
    "query_orchestrator",
    "query_router_service",
    "tool_registry",
]
