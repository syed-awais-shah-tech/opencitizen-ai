"""Typed exceptions for geospatial processing, validation, and conversion."""

from app.core.errors import AppException


class GeospatialError(AppException):
    """Base exception for geospatial operations."""

    def __init__(self, message: str, status_code: int = 400, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="GEOSPATIAL_ERROR",
            status_code=status_code,
            details=details,
        )


class GeospatialValidationError(GeospatialError):
    """Exception raised when geographic coordinates or GeoJSON structures fail validation."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=422, details=details)


class NoGeospatialDataError(GeospatialError):
    """Exception raised when a dataset does not contain valid spatial coordinate columns."""

    def __init__(self, identifier: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"No geographic coordinate or geometry columns detected in dataset '{identifier}'.",
            status_code=404,
            details=details,
        )
