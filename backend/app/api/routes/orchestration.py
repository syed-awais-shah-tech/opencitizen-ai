"""API routes for query orchestration and routing inspection."""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.orchestration.models import RouteRequest, RoutingDecision
from app.orchestration.router import query_router_service
from app.orchestration.tools import tool_registry

router = APIRouter(prefix="/orchestration", tags=["Orchestration"])


class ToolMetadata(BaseModel):
    name: str = Field(..., description="Name of the permitted tool.")
    description: str = Field(..., description="Capabilities and purpose of the tool.")
    allowed: bool = Field(default=True, description="Whether tool execution is permitted.")


@router.post(
    "/route",
    response_model=RoutingDecision,
    status_code=status.HTTP_200_OK,
    summary="Determine query routing category",
    description=(
        "Analyzes a natural language inquiry and determines whether it requires "
        "document retrieval (Qdrant), structured data analysis (DuckDB), both (hybrid), "
        "or neither / unsupported."
    ),
)
async def determine_query_route(payload: RouteRequest) -> RoutingDecision:
    """Classify inquiry into one of the four routing categories."""
    from app.core.security import sanitize_prompt_input

    clean_question = sanitize_prompt_input(payload.question)
    return query_router_service.classify(clean_question)


@router.get(
    "/tools",
    response_model=list[ToolMetadata],
    status_code=status.HTTP_200_OK,
    summary="List permitted explicit orchestration tools",
    description="Returns all registered, type-safe tools available to the controlled orchestration layer.",
)
async def list_orchestration_tools() -> list[ToolMetadata]:
    """List approved tools with descriptions."""
    tools = []
    for name in tool_registry.allowed_tool_names:
        tool = tool_registry.get_tool(name)
        tools.append(
            ToolMetadata(
                name=tool.name,
                description=tool.description,
                allowed=True,
            )
        )
    return tools
