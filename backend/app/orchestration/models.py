"""Data models and schemas for query orchestration and tool routing."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class RouteCategory(str, Enum):
    """The four discrete routing categories supported by the query orchestration layer."""

    DOCUMENT_RETRIEVAL = "document_retrieval"
    DATA_ANALYSIS = "data_analysis"
    BOTH = "both"
    UNSUPPORTED = "unsupported"


class RoutingDecision(BaseModel):
    """Structured outcome produced by the controlled router."""

    route: RouteCategory = Field(
        ...,
        description="Target routing category for the inquiry.",
        examples=["document_retrieval", "data_analysis", "both", "unsupported"],
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this routing path was determined.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Measured confidence score of the routing determination.",
    )
    target_table: Optional[str] = Field(
        default=None,
        description="Identified structured dataset table name if analytical query is needed.",
    )
    search_query: Optional[str] = Field(
        default=None,
        description="Refined text search query if document retrieval is needed.",
    )
    suggested_tools: list[str] = Field(
        default_factory=list,
        description="List of explicit permitted tool names to execute.",
    )


class RouteRequest(BaseModel):
    """Payload for requesting an explicit routing determination."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Civic question to classify.",
    )


class ToolCall(BaseModel):
    """Explicit validated tool invocation request."""

    name: str = Field(..., description="Name of the permitted tool.")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Validated argument dictionary."
    )


class ToolExecutionResult(BaseModel):
    """Outcome of an explicit tool invocation."""

    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
