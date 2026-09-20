"""OpenCitizen AI Analytics Package - Controlled DuckDB Analytical Engine."""

from app.analytics.engine import DuckDBEngine, duckdb_engine
from app.analytics.exceptions import (
    AnalysisPlanValidationError,
    AnalyticsError,
    ColumnNotFoundError,
    IncompatibleColumnTypeError,
    SQLValidationError,
    TableNotAllowedError,
)
from app.analytics.intent import IntentExtractor
from app.analytics.planner import QueryPlanner
from app.analytics.schemas import (
    AnalysisPlan,
    AnalyticalQueryRequest,
    AnalyticalResult,
    ChartConfig,
    ChartSeries,
    ChartType,
    FilterCondition,
    FormatType,
    SortCondition,
    TableSchemaInfo,
)
from app.analytics.validator import QueryValidator
from app.analytics.visualization import ChartGenerator

__all__ = [
    "DuckDBEngine",
    "duckdb_engine",
    "QueryValidator",
    "QueryPlanner",
    "IntentExtractor",
    "ChartGenerator",
    "AnalysisPlan",
    "AnalyticalQueryRequest",
    "AnalyticalResult",
    "ChartConfig",
    "ChartSeries",
    "ChartType",
    "FormatType",
    "FilterCondition",
    "SortCondition",
    "TableSchemaInfo",
    "AnalyticsError",
    "AnalysisPlanValidationError",
    "SQLValidationError",
    "TableNotAllowedError",
    "ColumnNotFoundError",
    "IncompatibleColumnTypeError",
]
