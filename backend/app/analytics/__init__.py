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
    FilterCondition,
    SortCondition,
    TableSchemaInfo,
)
from app.analytics.validator import QueryValidator

__all__ = [
    "DuckDBEngine",
    "duckdb_engine",
    "QueryValidator",
    "QueryPlanner",
    "IntentExtractor",
    "AnalysisPlan",
    "AnalyticalQueryRequest",
    "AnalyticalResult",
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
