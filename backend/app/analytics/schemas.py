"""Pydantic schemas and contract types for the DuckDB analytical service."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


OperationType = Literal["count", "sum", "average", "minimum", "maximum"]
FilterOperator = Literal[
    "=", "!=", ">", ">=", "<", "<=", "LIKE", "ILIKE", "IN", "IS NULL", "IS NOT NULL"
]
SortDirection = Literal["ASC", "DESC"]


class FilterCondition(BaseModel):
    """Filter constraint applied to an analytical dataset."""

    column: str = Field(..., description="Column identifier to filter on", min_length=1)
    operator: FilterOperator = Field(default="=", description="Comparison or membership operator")
    value: Any = Field(default=None, description="Operand value (scalar or list for IN)")

    @field_validator("column")
    @classmethod
    def validate_column_name(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or any(c in clean for c in ";'\"`\\/"):
            raise ValueError(f"Invalid column name in filter: {v}")
        return clean


class SortCondition(BaseModel):
    """Sorting directive for analytical query results."""

    column: str = Field(..., description="Column or metric alias to sort by", min_length=1)
    direction: SortDirection = Field(default="ASC", description="Sort order: ASC or DESC")

    @field_validator("column")
    @classmethod
    def validate_sort_column(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or any(c in clean for c in ";'\"`\\/"):
            raise ValueError(f"Invalid column name in sort: {v}")
        return clean


class AnalysisPlan(BaseModel):
    """Controlled, structured analytical plan.

    All natural language questions are translated into this explicit representation
    before any SQL is compiled and validated.
    """

    table_name: str = Field(..., description="Target database table identifier", min_length=1)
    operation: OperationType = Field(
        default="count",
        description="Primary analytical operation: count, sum, average, minimum, maximum",
    )
    target_column: Optional[str] = Field(
        default=None,
        description="Target column for the operation (required for sum, average, min, max; optional for count)",
    )
    group_by: list[str] = Field(
        default_factory=list,
        description="Columns to group by for dimensional aggregations",
    )
    filters: list[FilterCondition] = Field(
        default_factory=list,
        description="Filtering constraints to apply in WHERE clause",
    )
    sort_by: list[SortCondition] = Field(
        default_factory=list,
        description="Ordering criteria to apply in ORDER BY clause",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum rows to return (clamped to max 1000 for safety)",
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or any(c in clean for c in ";'\"`\\/ "):
            raise ValueError(f"Invalid table identifier: {v}")
        return clean

    @field_validator("group_by")
    @classmethod
    def sanitize_group_by(cls, v: list[str]) -> list[str]:
        sanitized = []
        for col in v:
            clean = col.strip().lower()
            if not clean or any(c in clean for c in ";'\"`\\/ "):
                raise ValueError(f"Invalid column identifier in group_by: {col}")
            if clean not in sanitized:
                sanitized.append(clean)
        return sanitized


class AnalyticalQueryRequest(BaseModel):
    """Request payload for executing a controlled analytical query."""

    question: Optional[str] = Field(
        default=None,
        description="Natural language question to parse into an analysis plan",
        examples=["What is the total expenditure by department in 2023?"],
    )
    table_name: Optional[str] = Field(
        default=None,
        description="Target table name (e.g. dept_expenses, vendor_contracts)",
    )
    dataset_id: Optional[str] = Field(
        default=None,
        description="Optional dataset ID registered in PostgreSQL metadata",
    )
    plan: Optional[AnalysisPlan] = Field(
        default=None,
        description="Explicit analysis plan (bypasses natural-language intent parsing if provided)",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Safety boundary for returned rows",
    )


ChartType = Literal["bar", "line", "pie", "table"]
FormatType = Literal["currency", "number", "percent", "integer", "string"]


class ChartSeries(BaseModel):
    """Configuration for a single metric series in a chart."""

    key: str = Field(..., description="Data key/column name for this series")
    label: str = Field(..., description="Display label for the legend/tooltip")
    color: str = Field(default="#06b6d4", description="Hex color or token for the series")
    format_type: FormatType = Field(default="number", description="Value formatting rule")


class ChartConfig(BaseModel):
    """Complete, self-contained chart configuration generated deterministically from analytical data."""

    chart_type: ChartType = Field(
        ..., description="Selected safe chart type: bar, line, pie, table"
    )
    title: str = Field(..., description="Descriptive title of the visualization")
    description: Optional[str] = Field(
        default=None, description="Contextual explanation or subtitle"
    )
    x_key: Optional[str] = Field(
        default=None, description="Dimension/category key for X-axis"
    )
    x_label: Optional[str] = Field(default=None, description="Label for X-axis")
    y_label: Optional[str] = Field(default=None, description="Label for Y-axis")
    series: list[ChartSeries] = Field(
        default_factory=list, description="Data series/metrics to plot"
    )
    data: list[dict[str, Any]] = Field(
        default_factory=list, description="Direct structured data points"
    )
    selection_reason: str = Field(
        ..., description="Deterministic rationale explaining why this chart type was selected"
    )
    is_empty: bool = Field(
        default=False, description="True if no data points or empty result set"
    )
    error_message: Optional[str] = Field(
        default=None, description="Description of any error or degraded state"
    )


class AnalyticalResult(BaseModel):
    """Structured result returned by the DuckDB analytical engine."""

    plan: AnalysisPlan = Field(..., description="The validated analysis plan executed")
    query_sql: str = Field(..., description="The exact validated SQL statement executed")
    columns: list[str] = Field(..., description="Column names returned in the result set")
    rows: list[dict[str, Any]] = Field(..., description="Result rows as structured dictionaries")
    row_count: int = Field(..., ge=0, description="Total rows in the result set")
    rows_scanned: int = Field(..., ge=0, description="Total rows scanned in the underlying table")
    execution_time_ms: float = Field(..., ge=0.0, description="DuckDB execution latency in ms")
    table_name: str = Field(..., description="Target table that was queried")
    derivation: str = Field(..., description="Human-readable mathematical explanation")
    chart: Optional[ChartConfig] = Field(
        default=None,
        description="Structured chart configuration automatically generated from analytical results",
    )


class TableColumnInfo(BaseModel):
    """Column definition for analytical tables."""

    name: str
    type: str  # VARCHAR, DOUBLE, INTEGER, DATE, BOOLEAN


class TableSchemaInfo(BaseModel):
    """Schema overview of an active DuckDB analytical table."""

    table_name: str
    columns: list[TableColumnInfo]
    row_count: int
