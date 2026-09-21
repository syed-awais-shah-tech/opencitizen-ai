"""API routes for controlled DuckDB analytical queries."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.analytics.exceptions import TableNotAllowedError
from app.analytics.schemas import (
    AnalyticalQueryRequest,
    AnalyticalResult,
    ChartConfig,
    TableSchemaInfo,
)
from app.analytics.visualization import ChartGenerator
from app.db.session import get_db
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post(
    "/query",
    response_model=AnalyticalResult,
    status_code=status.HTTP_200_OK,
    summary="Execute controlled analytical query",
    description="Execute an evidence-grounded analytical query over structured datasets using DuckDB. Follows question → intent plan → validated SQL → DuckDB execution.",
)
async def query_analytics(
    request: AnalyticalQueryRequest,
    db: Session = Depends(get_db),
) -> AnalyticalResult:
    """Execute controlled analytical query with safety boundaries."""
    return analytics_service.run_analytical_query(request=request, db=db)


@router.post(
    "/visualize",
    response_model=ChartConfig,
    status_code=status.HTTP_200_OK,
    summary="Generate chart configuration from analytical result",
    description="Deterministically generate an evidence-grounded chart configuration (bar, line, pie, or table) from structured analytical results.",
)
async def generate_visualization(
    result: AnalyticalResult,
) -> ChartConfig:
    """Generate safe chart configuration for structured data without LLM hallucination."""
    return ChartGenerator.generate(
        columns=result.columns,
        rows=result.rows,
        table_name=result.table_name,
        plan=result.plan,
        derivation=result.derivation,
    )


@router.get(
    "/tables",
    response_model=list[TableSchemaInfo],
    status_code=status.HTTP_200_OK,
    summary="List registered analytical tables",
    description="Retrieve all tables currently available in the DuckDB analytical engine with schema details.",
)
async def list_analytical_tables() -> list[TableSchemaInfo]:
    """List analytical tables and column types."""
    return analytics_service.list_tables()


@router.get(
    "/tables/{table_name}",
    response_model=TableSchemaInfo,
    status_code=status.HTTP_200_OK,
    summary="Get table schema",
    description="Retrieve column definitions and row count for an analytical table in DuckDB.",
)
async def get_table_info(table_name: str) -> TableSchemaInfo:
    """Get single table schema."""
    from app.core.security import validate_entity_id

    clean_name = validate_entity_id(table_name.strip().lower())
    if not analytics_service.engine.has_table(clean_name):
        raise TableNotAllowedError(clean_name, analytics_service.engine.get_registered_tables())
    return analytics_service.engine.get_table_info(clean_name)
