"""Domain exceptions for the DuckDB analytical engine and query validation."""

from typing import Any
from fastapi import status
from app.core.errors import AppException


class AnalyticsError(AppException):
    """Base exception for all analytical query engine errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ANALYTICS_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class AnalysisPlanValidationError(AnalyticsError):
    """Raised when an analytical intent/plan fails semantic or schema validation."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            error_code="ANALYSIS_PLAN_INVALID",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )


class SQLValidationError(AnalyticsError):
    """Raised when SQL fails security, syntax, or AST policy validation."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            error_code="SQL_VALIDATION_FAILED",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )


class TableNotAllowedError(AnalyticsError):
    """Raised when a query attempts to access an unregistered or unapproved table."""

    def __init__(self, table_name: str, allowed_tables: list[str] | None = None) -> None:
        super().__init__(
            message=f"Table '{table_name}' is not registered or not permitted for analytical queries.",
            error_code="TABLE_NOT_ALLOWED",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"table_name": table_name, "allowed_tables": allowed_tables or []},
        )


class ColumnNotFoundError(AnalyticsError):
    """Raised when an operation, filter, or grouping references a non-existent column."""

    def __init__(self, column_name: str, table_name: str, available_columns: list[str]) -> None:
        super().__init__(
            message=f"Column '{column_name}' does not exist in table '{table_name}'.",
            error_code="COLUMN_NOT_FOUND",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details={
                "column_name": column_name,
                "table_name": table_name,
                "available_columns": available_columns,
            },
        )


class IncompatibleColumnTypeError(AnalyticsError):
    """Raised when an operation is mathematically invalid for a column's data type."""

    def __init__(self, operation: str, column_name: str, column_type: str) -> None:
        super().__init__(
            message=f"Operation '{operation}' cannot be performed on column '{column_name}' of type '{column_type}'.",
            error_code="INCOMPATIBLE_COLUMN_TYPE",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details={
                "operation": operation,
                "column_name": column_name,
                "column_type": column_type,
            },
        )


class ExecutionLimitExceededError(AnalyticsError):
    """Raised when a query violates row limits or resource boundaries."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            error_code="LIMIT_EXCEEDED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )
