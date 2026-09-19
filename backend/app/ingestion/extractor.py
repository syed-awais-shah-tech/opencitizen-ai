"""PDF text extraction engine with page-level integrity preservation."""

import io
from pathlib import Path
from typing import BinaryIO
import pypdf
from pypdf.errors import EmptyFileError, PdfReadError

from app.ingestion.cleaner import TextCleaner
from app.ingestion.exceptions import (
    EmptyPDFError,
    ExtractionError,
    InvalidPDFError,
)
from app.ingestion.models import ExtractedPage


class PDFExtractor:
    """Extracts text content page-by-page from PDF files while preserving page numbers."""

    def __init__(self, cleaner: TextCleaner | None = None) -> None:
        self.cleaner = cleaner or TextCleaner()

    def extract_from_bytes(self, content: bytes) -> list[ExtractedPage]:
        """Extract pages from in-memory byte buffer."""
        if not content or len(content) == 0:
            raise EmptyPDFError("Uploaded PDF content is empty (0 bytes).")

        # Validate PDF signature (%PDF-)
        if not content.startswith(b"%PDF-"):
            raise InvalidPDFError("File does not start with standard '%PDF-' header signature.")

        stream = io.BytesIO(content)
        return self._extract_from_stream(stream)

    def extract_from_file(self, file_path: str | Path) -> list[ExtractedPage]:
        """Extract pages from a filesystem file path."""
        path = Path(file_path)
        if not path.exists():
            raise InvalidPDFError(f"PDF file does not exist at '{path}'.")

        if path.stat().st_size == 0:
            raise EmptyPDFError(f"PDF file at '{path}' is empty (0 bytes).")

        try:
            with open(path, "rb") as f:
                content = f.read()
            return self.extract_from_bytes(content)
        except (InvalidPDFError, EmptyPDFError):
            raise
        except Exception as exc:
            raise ExtractionError(f"Failed to read file at '{path}': {exc}") from exc

    def _extract_from_stream(self, stream: BinaryIO) -> list[ExtractedPage]:
        """Extract pages using pypdf.PdfReader."""
        try:
            reader = pypdf.PdfReader(stream)
        except EmptyFileError as exc:
            raise EmptyPDFError("PDF stream is empty.") from exc
        except PdfReadError as exc:
            raise InvalidPDFError(f"Malformed or unreadable PDF: {exc}") from exc
        except Exception as exc:
            raise InvalidPDFError(f"Failed to parse PDF document: {exc}") from exc

        # Check for encryption
        if reader.is_encrypted:
            try:
                # Attempt decrypt with empty password for standard protected documents
                decrypted = reader.decrypt("")
                if decrypted == 0:
                    raise ExtractionError("PDF document is password-protected and cannot be read.")
            except Exception as exc:
                raise ExtractionError(f"Failed to decrypt password-protected PDF: {exc}") from exc

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise EmptyPDFError("PDF document contains 0 pages.")

        extracted_pages: list[ExtractedPage] = []

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                raw_text = page.extract_text() or ""
            except Exception as exc:
                # Log or handle corrupted page gracefully
                raw_text = ""

            cleaned_text = self.cleaner.clean(raw_text)
            is_insufficient = self.cleaner.is_insufficient(cleaned_text)

            extracted_pages.append(
                ExtractedPage(
                    page_number=page_num,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    char_count=len(cleaned_text),
                    is_empty=is_insufficient,
                )
            )

        return extracted_pages
