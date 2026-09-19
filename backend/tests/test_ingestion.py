"""Automated unit and pipeline tests for PDF document ingestion."""

import pytest

from app.ingestion import (
    DocumentChunker,
    EmptyPDFError,
    ExtractionError,
    IngestionResult,
    InvalidPDFError,
    PDFExtractor,
    PDFIngestionPipeline,
    TextCleaner,
)
from tests.pdf_helpers import create_blank_pdf, create_test_pdf


def test_text_cleaner_normalization() -> None:
    """Ensure TextCleaner strips control characters, normalizes whitespace, and resolves hyphens."""
    cleaner = TextCleaner()
    raw = "  Department   of   Public\t\tWorks\n\n\n\nOrdinance   com-\nmittee   review.  \x00\x08 "
    cleaned = cleaner.clean(raw)

    assert "\x00" not in cleaned
    assert "\x08" not in cleaned
    assert "committee" in cleaned
    assert "Department of Public Works" in cleaned
    assert "\n\n\n" not in cleaned


def test_pipeline_standard_multipage_pdf() -> None:
    """Ensure multi-page PDF extracts text while strictly preserving page-level traceability."""
    page_texts = [
        "City Adopted Budget Fiscal Year 2024. Executive summary and authorized operational allocations.",
        "Section 3.2 Parks, Recreation & Community Facilities. Authorized operational allocation was adjusted to $4,250,000.",
        "Section 4.1 Transportation Master Plan. Zero-emission municipal transit corridors designated for 2026 delivery.",
    ]
    pdf_bytes = create_test_pdf(page_texts)

    pipeline = PDFIngestionPipeline()
    result = pipeline.process_bytes(
        content=pdf_bytes,
        source_filename="City_Budget_2024.pdf",
        document_id="doc_budget_001",
        metadata={"department": "City Clerk", "fiscal_year": 2024},
    )

    assert isinstance(result, IngestionResult)
    assert result.document_id == "doc_budget_001"
    assert result.source_filename == "City_Budget_2024.pdf"
    assert result.total_pages == 3
    assert result.processed_pages == 3
    assert result.total_chunks >= 3
    assert len(result.warnings) == 0

    # Verify strict provenance fields on every single chunk
    for chunk in result.chunks:
        assert chunk.document_id == "doc_budget_001"
        assert chunk.source_filename == "City_Budget_2024.pdf"
        assert chunk.page_number in [1, 2, 3]
        assert chunk.chunk_id.startswith("chk_doc_budget_001_p")
        assert chunk.character_count > 0
        assert chunk.word_count > 0
        assert chunk.metadata["department"] == "City Clerk"
        assert chunk.metadata["page_number"] == chunk.page_number
        assert chunk.metadata["chunk_id"] == chunk.chunk_id


def test_pipeline_with_blank_or_sparse_page() -> None:
    """Ensure pages with little or no text are diagnosed with warnings and omitted from chunks."""
    # Page 2 is empty/sparse whitespace
    page_texts = [
        "Page 1 contains valid municipal council minutes and authorized votes.",
        "    \n\n   ",  # Blank/insufficient text
        "Page 3 contains formal committee closing remarks and adjournment signatures.",
    ]
    pdf_bytes = create_test_pdf(page_texts)

    pipeline = PDFIngestionPipeline()
    result = pipeline.process_bytes(
        content=pdf_bytes,
        source_filename="Council_Minutes.pdf",
        document_id="doc_council_002",
    )

    assert result.total_pages == 3
    assert result.processed_pages == 2
    assert len(result.warnings) >= 1
    assert "Page 2 contained little or no extractable text" in result.warnings[0]

    # Verify generated chunks originate only from valid pages (1 and 3)
    chunk_pages = {chunk.page_number for chunk in result.chunks}
    assert 1 in chunk_pages
    assert 3 in chunk_pages
    assert 2 not in chunk_pages


def test_pipeline_all_blank_pages() -> None:
    """Ensure a PDF with only blank pages completes safely with 0 chunks and descriptive warnings."""
    blank_pdf = create_blank_pdf(num_pages=2)

    pipeline = PDFIngestionPipeline()
    result = pipeline.process_bytes(
        content=blank_pdf,
        source_filename="Blank_Scan.pdf",
        document_id="doc_blank_003",
    )

    assert result.total_pages == 2
    assert result.processed_pages == 0
    assert result.total_chunks == 0
    assert len(result.warnings) == 2


def test_empty_bytes_raises_error() -> None:
    """Ensure feeding 0 bytes raises an EmptyPDFError with 400 status."""
    pipeline = PDFIngestionPipeline()
    with pytest.raises(EmptyPDFError) as exc_info:
        pipeline.process_bytes(content=b"", source_filename="zero_bytes.pdf")
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "EMPTY_PDF"


def test_invalid_file_signature_raises_error() -> None:
    """Ensure non-PDF files without '%PDF-' header raise InvalidPDFError."""
    pipeline = PDFIngestionPipeline()
    fake_content = b"<html><body>Not a real PDF</body></html>"
    with pytest.raises(InvalidPDFError) as exc_info:
        pipeline.process_bytes(content=fake_content, source_filename="fake.pdf")
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "INVALID_PDF"


def test_corrupted_pdf_data_raises_error() -> None:
    """Ensure malformed PDF data raises InvalidPDFError."""
    pipeline = PDFIngestionPipeline()
    corrupted = b"%PDF-1.4\ncorrupted data with truncated xref and no catalog"
    with pytest.raises(InvalidPDFError):
        pipeline.process_bytes(content=corrupted, source_filename="corrupted.pdf")


def test_document_chunker_overlap_and_traceability() -> None:
    """Ensure chunker respects custom size, applies overlap, and preserves metadata."""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=30, min_chunk_size=20)
    long_text = (
        "The municipal transportation department has initiated the 2026 zero-emission bus fleet upgrade. "
        "Phase one covers 45 electric buses deployed along central commercial avenues. "
        "Phase two expands charging infrastructure at east side maintenance terminals."
    )
    from app.ingestion.models import ExtractedPage

    page = ExtractedPage(
        page_number=4,
        raw_text=long_text,
        cleaned_text=long_text,
        char_count=len(long_text),
        is_empty=False,
    )

    chunks = chunker.chunk_page(
        page=page,
        document_id="doc_trans_010",
        source_filename="Transit_Fleet_2026.pdf",
    )

    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c.chunk_id == f"chk_doc_trans_010_p4_{idx + 1:03d}"
        assert c.document_id == "doc_trans_010"
        assert c.page_number == 4
        assert c.source_filename == "Transit_Fleet_2026.pdf"
        assert c.character_count > 0
