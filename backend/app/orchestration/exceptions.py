"""Domain exceptions for query orchestration, tool validation, and routing."""

from typing import Any
from fastapi import status
from app.core.errors import AppException


class OrchestrationError(AppException):
    """Base exception for all query orchestration errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ORCHESTRATION_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class ToolNotPermittedError(OrchestrationError):
    """Raised when an unapproved, unverified, or arbitrary tool invocation is attempted.

    Prevents models or callers from attempting arbitrary SQL execution, database connections,
    or non-whitelisted execution pathways.
    """

    def __init__(self, tool_name: str, allowed_tools: list[str] | None = None) -> None:
        super().__init__(
            message=f"Tool '{tool_name}' is not permitted. Only validated explicit tools may be invoked.",
            error_code="TOOL_NOT_PERMITTED",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"tool_name": tool_name, "allowed_tools": allowed_tools or []},
        )


class ToolArgumentValidationError(OrchestrationError):
    """Raised when parameters passed to an explicit tool fail validation."""

    def __init__(self, tool_name: str, reason: str, details: Any = None) -> None:
        super().__init__(
            message=f"Validation failed for tool '{tool_name}': {reason}",
            error_code="TOOL_ARGUMENT_INVALID",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )


class RoutingClassificationError(OrchestrationError):
    """Raised when query classification fails or yields an invalid routing decision."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            error_code="ROUTING_CLASSIFICATION_FAILED",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )
