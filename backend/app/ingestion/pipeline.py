"""End-to-end PDF document ingestion and chunking pipeline."""

import time
import uuid
from pathlib import Path
from typing import Any

from app.ingestion.chunker import DocumentChunker
from app.ingestion.extractor import PDFExtractor
from app.ingestion.models import IngestionResult


class PDFIngestionPipeline:
    """Orchestrates PDF validation, text extraction, page preservation, and chunking."""

    def __init__(
        self,
        extractor: PDFExtractor | None = None,
        chunker: DocumentChunker | None = None,
    ) -> None:
        self.extractor = extractor or PDFExtractor()
        self.chunker = chunker or DocumentChunker()

    def process_bytes(
        self,
        content: bytes,
        source_filename: str,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Process in-memory PDF byte stream into traceable document chunks."""
        start_time = time.perf_counter()
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:12]}"

        # 1. Extract pages with page-level integrity
        extracted_pages = self.extractor.extract_from_bytes(content)

        # 2. Inspect pages and collect diagnostics
        warnings: list[str] = []
        valid_pages = []

        for page in extracted_pages:
            if page.is_empty:
                warnings.append(
                    f"Page {page.page_number} contained little or no extractable text (length={page.char_count})."
                )
            else:
                valid_pages.append(page)

        # 3. Chunk valid pages while preserving page numbers and metadata
        chunks = self.chunker.chunk_pages(
            pages=valid_pages,
            document_id=doc_id,
            source_filename=source_filename,
            base_metadata=metadata,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return IngestionResult(
            document_id=doc_id,
            source_filename=source_filename,
            total_pages=len(extracted_pages),
            processed_pages=len(valid_pages),
            total_chunks=len(chunks),
            chunks=chunks,
            warnings=warnings,
            processing_time_ms=elapsed_ms,
        )

    def process_file(
        self,
        file_path: str | Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Process PDF file from filesystem path."""
        path = Path(file_path)
        with open(path, "rb") as f:
            content = f.read()
        return self.process_bytes(
            content=content,
            source_filename=path.name,
            document_id=document_id,
            metadata=metadata,
        )


pipeline = PDFIngestionPipeline()
