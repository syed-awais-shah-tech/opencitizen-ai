"""Centralized error handling and domain exceptions for OpenCitizen AI API."""

from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base exception class for all domain-specific API errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details


class EntityNotFoundError(AppException):
    """Raised when a requested resource or entity is not found."""

    def __init__(self, entity_name: str, entity_id: str) -> None:
        super().__init__(
            message=f"{entity_name} with identifier '{entity_id}' not found.",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationException(AppException):
    """Raised when request payload or business validation fails."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=getattr(
                status, "HTTP_422_UNPROCESSABLE_CONTENT", 422
            ),
            details=details,
        )


class QueryProcessingError(AppException):
    """Raised when the natural language query pipeline fails to process an inquiry."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            error_code="QUERY_PROCESSING_FAILED",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        _request: Request, exc: AppException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=getattr(
                status, "HTTP_422_UNPROCESSABLE_CONTENT", 422
            ),
            content={
                "success": False,
                "error_code": "REQUEST_VALIDATION_ERROR",
                "message": "Invalid request payload or query parameters.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": None,
            },
        )
