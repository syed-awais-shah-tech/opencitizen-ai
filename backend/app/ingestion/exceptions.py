"""Custom domain exceptions for document ingestion and text extraction."""

from app.core.errors import AppException


class IngestionError(AppException):
    """Base exception for document ingestion pipeline failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "INGESTION_ERROR",
        status_code: int = 400,
        details: object = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class EmptyPDFError(IngestionError):
    """Raised when an uploaded PDF has 0 bytes or 0 pages."""

    def __init__(self, message: str = "PDF document is empty (0 pages or 0 bytes).") -> None:
        super().__init__(
            message=message,
            error_code="EMPTY_PDF",
            status_code=400,
        )


class InvalidPDFError(IngestionError):
    """Raised when an uploaded file is not a valid or readable PDF format."""

    def __init__(self, message: str = "Invalid PDF file structure or corrupted header.") -> None:
        super().__init__(
            message=message,
            error_code="INVALID_PDF",
            status_code=400,
        )


class ExtractionError(IngestionError):
    """Raised when text extraction fails due to encryption or corrupted page streams."""

    def __init__(
        self,
        message: str = "Failed to extract text streams from PDF.",
        details: object = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="EXTRACTION_FAILURE",
            status_code=422,
            details=details,
        )


class UnsupportedDatasetFormatError(IngestionError):
    """Raised when an uploaded structured dataset is not a supported format (CSV, XLSX, JSON)."""

    def __init__(
        self,
        message: str = "Unsupported dataset format. OpenCitizen AI supports CSV, XLSX, and JSON.",
    ) -> None:
        super().__init__(
            message=message,
            error_code="UNSUPPORTED_DATASET_FORMAT",
            status_code=400,
        )


class DatasetValidationError(IngestionError):
    """Raised when dataset structure, schema, or content fails ingestion validation."""

    def __init__(
        self,
        message: str = "Dataset validation failed.",
        details: object = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="DATASET_VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
