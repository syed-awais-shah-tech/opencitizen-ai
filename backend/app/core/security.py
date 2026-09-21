"""Security utilities, input sanitization, file upload boundaries, and secret protection."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile, status
from app.core.config import settings
from app.core.errors import AppException

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 Megabytes
DEFAULT_MAX_QUESTION_LENGTH = 2000  # 2000 characters
CHUNK_READ_SIZE = 64 * 1024  # 64 KB read buffer

# Known file signature magic bytes
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "parquet": [b"PAR1"],
    "xlsx": [b"PK\x03\x04"],
    "json": [b"{", b"[", b" "],
}

# Regex for entity IDs (prevents path traversal like ../../etc/passwd)
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# Regex for prompt injection / jailbreak patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(?:in\s+)?developer\s+mode\b", re.IGNORECASE),
    re.compile(r"\bbypass\s+(?:safety|rules|instructions|filter)\b", re.IGNORECASE),
    re.compile(r"\boutput\s+all\s+(?:system\s+prompts?|instructions?|api[_\s-]?keys?)\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(?:the\s+)?(?:system\s+prompt|rules|previous\s+instructions)\b", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]", re.IGNORECASE),
    re.compile(r"---\s*EVIDENCE\s+EXCERPT\s*\[\d+\]\s*---", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(?:an?\s+)?unrestricted\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
]

# Sensitive credential patterns for scrubbing
SECRET_PATTERNS = [
    (re.compile(r"(AIza[0-9A-Za-z-_]{35})"), "AIza[MASKED_API_KEY]"),
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_.-]{16,}", re.IGNORECASE), r"\1[MASKED_TOKEN]"),
    (re.compile(r"(://[^:]+:)([^@]+)(@)"), r"\1[MASKED_PASSWORD]\3"),
    (re.compile(r"(password[\"']?\s*[:=]\s*[\"'])([^\"']+)([\"'])", re.IGNORECASE), r"\1[MASKED]\3"),
]


# ==============================================================================
# Security Exceptions
# ==============================================================================


class SecurityError(AppException):
    """Base exception for all security boundary violations."""

    def __init__(
        self,
        message: str,
        error_code: str = "SECURITY_VIOLATION",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=status_code)


class OversizedUploadError(SecurityError):
    """Raised when an uploaded file exceeds the maximum permitted size limit."""

    def __init__(self, size_bytes: int, max_bytes: int) -> None:
        size_mb = size_bytes / (1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)
        super().__init__(
            message=f"Uploaded file size ({size_mb:.2f} MB) exceeds maximum permitted size of {max_mb:.2f} MB.",
            error_code="OVERSIZED_UPLOAD",
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
        )


class InvalidFileFormatError(SecurityError):
    """Raised when an uploaded file extension or signature is rejected."""

    def __init__(self, message: str, error_code: str = "INVALID_FILE_FORMAT") -> None:
        super().__init__(message=message, error_code=error_code, status_code=status.HTTP_400_BAD_REQUEST)


class MaliciousInputError(SecurityError):
    """Raised when input contains malicious payload or injection patterns."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, error_code="MALICIOUS_INPUT_DETECTED", status_code=status.HTTP_400_BAD_REQUEST)


class UnsafeIdentifierError(SecurityError):
    """Raised when an entity ID violates safe formatting or attempts path traversal."""

    def __init__(self, entity_id: str) -> None:
        super().__init__(
            message=f"Invalid entity identifier: '{entity_id}'. IDs must contain only alphanumeric, hyphen, and underscore characters.",
            error_code="UNSAFE_IDENTIFIER",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# ==============================================================================
# Security Functions
# ==============================================================================


def sanitize_filename(raw_name: str | None, default_name: str = "upload.bin") -> str:
    """Sanitize user-provided filename preventing path traversal, null bytes, and unsafe characters."""
    if not raw_name or not raw_name.strip():
        return default_name

    # Normalize backslashes to forward slashes and take the basename
    cleaned = raw_name.strip().replace("\\", "/").rstrip("/")
    basename = cleaned.split("/")[-1]

    # Strip null bytes and control characters
    name = "".join(ch for ch in basename if ch.isprintable() and ch not in "\0\r\n\t")

    # Replace forbidden path characters: / \ : * ? " < > |
    name = re.sub(r'[/\\:*?"<>|]', "_", name)

    # Prevent hidden files and empty names
    name = name.lstrip(".")
    if not name:
        return default_name

    # Truncate length
    if len(name) > 255:
        stem = Path(name).stem[:240]
        ext = Path(name).suffix[:14]
        name = f"{stem}{ext}"

    return name


def validate_entity_id(entity_id: str) -> str:
    """Validate that an entity identifier (document_id, dataset_id) contains no path traversal."""
    if not entity_id or not SAFE_IDENTIFIER_PATTERN.match(entity_id):
        raise UnsafeIdentifierError(entity_id)
    return entity_id


async def validate_file_upload(
    file: UploadFile,
    allowed_extensions: set[str],
    max_size_bytes: int = DEFAULT_MAX_UPLOAD_SIZE_BYTES,
    error_code: str = "INVALID_FILE_FORMAT",
) -> bytes:
    """Read and validate uploaded file in bounded chunks, checking size and signature."""
    filename = sanitize_filename(file.filename)
    ext = Path(filename).suffix.lower()

    if ext not in allowed_extensions:
        raise InvalidFileFormatError(
            f"File extension '{ext}' is not supported. Allowed formats: {sorted(allowed_extensions)}",
            error_code=error_code,
        )

    # Read content in chunks to prevent unbounded memory exhaustion
    total_bytes = 0
    chunks: list[bytes] = []

    while True:
        chunk = await file.read(CHUNK_READ_SIZE)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_size_bytes:
            raise OversizedUploadError(size_bytes=total_bytes, max_bytes=max_size_bytes)
        chunks.append(chunk)

    content = b"".join(chunks)

    if len(content) == 0:
        raise InvalidFileFormatError("Uploaded file is empty (0 bytes).", error_code=error_code)

    # Magic byte verification
    clean_ext = ext.lstrip(".")
    if clean_ext == "pdf":
        if not content.startswith(b"%PDF-"):
            raise InvalidFileFormatError(
                "File does not start with valid PDF magic bytes ('%PDF-').",
                error_code=error_code,
            )
    elif clean_ext in ("parquet", "pq"):
        if not content.startswith(b"PAR1"):
            raise InvalidFileFormatError(
                "File does not start with valid Parquet magic bytes ('PAR1').",
                error_code=error_code,
            )
    elif clean_ext == "xlsx":
        if not content.startswith(b"PK\x03\x04"):
            raise InvalidFileFormatError(
                "File does not start with valid XLSX/ZIP magic bytes ('PK\\x03\\x04').",
                error_code=error_code,
            )
    elif clean_ext == "csv":
        # Ensure CSV is textual and does not contain null bytes
        if b"\x00" in content[:4096]:
            raise InvalidFileFormatError(
                "Binary null bytes detected in CSV file.",
                error_code=error_code,
            )
    elif clean_ext == "json":
        stripped = content.strip()
        if not (stripped.startswith(b"{") or stripped.startswith(b"[")):
            raise InvalidFileFormatError(
                "File does not contain valid JSON object or array structure.",
                error_code=error_code,
            )

    return content


def sanitize_prompt_input(question: str, max_chars: int = DEFAULT_MAX_QUESTION_LENGTH) -> str:
    """Sanitize user natural language queries and guard against prompt injection attacks."""
    if not question or not question.strip():
        raise MaliciousInputError("Inquiry question cannot be empty.")

    cleaned = question.strip()

    if len(cleaned) > max_chars:
        raise MaliciousInputError(
            f"Inquiry text length ({len(cleaned)} characters) exceeds maximum allowed length of {max_chars} characters."
        )

    # Strip null bytes, non-printable control characters, and Unicode BiDi overrides
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() and ch not in "\0\u202E\u202D\u202C")

    # Check for obvious injection attack payloads
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(cleaned):
            logger.warning("Prompt injection pattern detected in user query: %s", pattern.pattern)
            raise MaliciousInputError("Prohibited prompt override or injection syntax detected in inquiry.")

    return cleaned


def scrub_secrets(text: str) -> str:
    """Redact sensitive API keys, passwords, and authorization tokens from text or log messages."""
    if not text:
        return text
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
