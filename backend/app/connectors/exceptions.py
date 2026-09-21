"""Exceptions for public-data connectors and external ingestion workflows."""

from __future__ import annotations

from fastapi import status
from app.core.errors import AppException


class ConnectorError(AppException):
    """Base exception for all connector-related failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "CONNECTOR_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=status_code)


class ConnectorFetchError(ConnectorError):
    """Raised when an external data source cannot be fetched (HTTP error, timeout, DNS failure)."""

    def __init__(self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY) -> None:
        super().__init__(
            message=message,
            error_code="CONNECTOR_FETCH_ERROR",
            status_code=status_code,
        )


class ConnectorValidationError(ConnectorError):
    """Raised when external data fails structural, security, or format validation."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="CONNECTOR_VALIDATION_ERROR",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        )


class ConnectorNormalizationError(ConnectorError):
    """Raised when external data cannot be normalized into standard tabular format."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="CONNECTOR_NORMALIZATION_ERROR",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        )
