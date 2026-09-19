"""Data pipeline document ingestion interface."""

import sys
from pathlib import Path

# Ensure backend root is available for imports
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.ingestion import (
    DocumentChunk,
    DocumentChunker,
    EmptyPDFError,
    ExtractedPage,
    ExtractionError,
    IngestionError,
    IngestionResult,
    InvalidPDFError,
    PDFExtractor,
    PDFIngestionPipeline,
    TextCleaner,
    pipeline,
)

__all__ = [
    "TextCleaner",
    "PDFExtractor",
    "DocumentChunker",
    "PDFIngestionPipeline",
    "pipeline",
    "DocumentChunk",
    "ExtractedPage",
    "IngestionResult",
    "IngestionError",
    "EmptyPDFError",
    "InvalidPDFError",
    "ExtractionError",
]
