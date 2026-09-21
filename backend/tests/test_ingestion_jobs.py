"""Automated tests for background ingestion jobs, worker pipeline lifecycle, and failure handling.

Stage 16 verification:
- Non-blocking HTTP upload flow: upload -> create job -> return queued status -> background execution
- End-to-end pipeline progression: queued -> extraction -> chunking -> embedding -> vector_storage -> completed
- Failure handling: corrupted files, pipeline exceptions, failed job & document status transitions
- Status polling endpoints: /documents/jobs/{job_id} and /documents/{document_id}/status
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.ingestion_job import IngestionJob
from app.services.ingestion_worker import IngestionWorkerService, ingestion_worker
from tests.pdf_helpers import create_test_pdf


def test_upload_non_blocking_returns_queued_job(client: TestClient) -> None:
    """Ensure POST /api/v1/documents/upload returns HTTP 201 immediately with queued status."""
    pdf_bytes = create_test_pdf([
        "Page 1: Civic transit budget allocation and fleet electrification plan.",
        "Page 2: Route optimization and charging infrastructure milestones.",
    ])

    files = {"file": ("transit_plan_2025.pdf", pdf_bytes, "application/pdf")}
    data = {
        "department": "Transportation",
        "category": "Infrastructure",
        "summary": "Fleet electrification overview.",
        "sync": "false",
    }

    # Upload non-blocking (default)
    response = client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()

    assert res_data["job_id"].startswith("job_")
    assert res_data["job_status"] == "queued"
    assert res_data["document"]["status"] == "queued"
    assert res_data["document"]["title"] == "transit_plan_2025.pdf"

    job_id = res_data["job_id"]
    doc_id = res_data["document"]["id"]

    # Poll until background thread completes (or timeout)
    max_wait_seconds = 5.0
    start = time.time()
    final_status = "queued"

    while time.time() - start < max_wait_seconds:
        job_res = client.get(f"/api/v1/documents/jobs/{job_id}")
        assert job_res.status_code == 200
        job_data = job_res.json()
        final_status = job_data["status"]
        if final_status in ("completed", "failed"):
            break
        time.sleep(0.05)

    assert final_status == "completed"
    assert job_data["stage"] == "completed"
    assert job_data["progress_pct"] == 100
    assert job_data["total_pages"] == 2
    assert job_data["total_chunks"] >= 2
    assert job_data["error_message"] is None
    assert job_data["processing_time_ms"] > 0

    # Verify document status polling endpoint
    status_res = client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_res.status_code == 200
    doc_status = status_res.json()
    assert doc_status["status"] == "completed"
    assert doc_status["job_status"] == "completed"
    assert doc_status["progress_pct"] == 100


def test_upload_sync_executes_inline(client: TestClient) -> None:
    """Ensure POST /api/v1/documents/upload with sync=true processes synchronously before returning."""
    pdf_bytes = create_test_pdf([
        "Section 1: Parks and recreation capital improvements.",
    ])

    files = {"file": ("parks_report.pdf", pdf_bytes, "application/pdf")}
    data = {
        "department": "Parks",
        "category": "Recreation",
        "sync": "true",
    }

    response = client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()

    assert res_data["job_status"] == "completed"
    assert res_data["total_pages"] == 1
    assert res_data["total_chunks"] >= 1
    assert res_data["document"]["status"] == "completed"
    assert res_data["processing_time_ms"] > 0


def test_get_job_status_endpoint(client: TestClient, db_session: Session) -> None:
    """Verify GET /api/v1/documents/jobs/{job_id} returns all job fields accurately."""
    # Seed a document and an ingestion job in database
    doc = Document(
        id="doc_test_12345",
        title="housing_strategy.pdf",
        department="Housing",
        category="Policy",
        page_count=10,
        chunk_count=25,
        file_size_bytes=1024,
        status="processing",
    )
    db_session.add(doc)

    job = IngestionJob(
        id="job_test_lifecycle_1",
        document_id="doc_test_12345",
        status="processing",
        stage="chunking",
        progress_pct=45,
        total_pages=10,
        processed_pages=10,
        total_chunks=0,
    )
    db_session.add(job)
    db_session.commit()

    response = client.get("/api/v1/documents/jobs/job_test_lifecycle_1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "job_test_lifecycle_1"
    assert data["document_id"] == "doc_test_12345"
    assert data["status"] == "processing"
    assert data["stage"] == "chunking"
    assert data["progress_pct"] == 45
    assert data["total_pages"] == 10


def test_get_document_jobs_list(client: TestClient, db_session: Session) -> None:
    """Verify GET /api/v1/documents/{doc_id}/jobs returns all historical jobs for a document."""
    doc = Document(
        id="doc_multi_jobs",
        title="zoning_ordinance.pdf",
        department="Planning",
        category="Zoning",
        status="completed",
    )
    db_session.add(doc)

    job1 = IngestionJob(
        id="job_attempt_1",
        document_id="doc_multi_jobs",
        status="failed",
        stage="failed",
        error_message="First attempt timed out",
    )
    job2 = IngestionJob(
        id="job_attempt_2",
        document_id="doc_multi_jobs",
        status="completed",
        stage="completed",
        progress_pct=100,
    )
    db_session.add_all([job1, job2])
    db_session.commit()

    response = client.get("/api/v1/documents/doc_multi_jobs/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2
    job_ids = [j["id"] for j in jobs]
    assert "job_attempt_1" in job_ids
    assert "job_attempt_2" in job_ids


def test_document_status_polling_endpoint(client: TestClient, db_session: Session) -> None:
    """Verify GET /api/v1/documents/{doc_id}/status provides unified document/job state."""
    doc = Document(
        id="doc_polling_test",
        title="water_quality_report.pdf",
        department="Utilities",
        category="Environmental",
        status="processing",
    )
    job = IngestionJob(
        id="job_polling_test",
        document_id="doc_polling_test",
        status="processing",
        stage="embedding",
        progress_pct=70,
        total_pages=5,
        total_chunks=12,
    )
    db_session.add_all([doc, job])
    db_session.commit()

    response = client.get("/api/v1/documents/doc_polling_test/status")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc_polling_test"
    assert data["title"] == "water_quality_report.pdf"
    assert data["status"] == "processing"
    assert data["job_id"] == "job_polling_test"
    assert data["job_status"] == "processing"
    assert data["stage"] == "embedding"
    assert data["progress_pct"] == 70


def test_job_failure_on_corrupted_pdf(client: TestClient, db_session: Session) -> None:
    """Ensure worker gracefully handles extraction failure, marks job and document as failed."""
    # Create corrupted bytes with PDF magic header to pass upload validation but fail pypdf extraction
    corrupted_pdf_bytes = b"%PDF-1.4\n%%EOF\nThis is completely invalid binary garbage that cannot be read as a PDF."

    files = {"file": ("corrupted_report.pdf", corrupted_pdf_bytes, "application/pdf")}
    data = {
        "department": "Audit",
        "category": "Reports",
        "sync": "true",  # run synchronously to immediately inspect the failure result
    }

    response = client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()

    job_id = res_data["job_id"]
    doc_id = res_data["document"]["id"]

    # Verify job record reflects failure
    job_res = client.get(f"/api/v1/documents/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "failed"
    assert job_data["stage"] == "failed"
    assert job_data["error_message"] is not None
    assert len(job_data["error_message"]) > 0

    # Verify document record reflects failure
    status_res = client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "failed"
    assert status_data["job_status"] == "failed"
    assert status_data["error_message"] is not None


def test_job_failure_on_vector_indexing_error(db_session: Session) -> None:
    """Ensure worker marks job and document as failed when vector indexing throws an unexpected error."""
    # Prepare a test document and job
    doc = Document(
        id="doc_err_vector",
        title="budget_memo.pdf",
        department="Finance",
        category="Budget",
        status="queued",
    )
    job = IngestionJob(
        id="job_err_vector",
        document_id="doc_err_vector",
        status="queued",
        stage="queued",
    )
    db_session.add_all([doc, job])
    db_session.commit()

    pdf_bytes = create_test_pdf(["Page 1: General ledger adjustments."])

    # Mock vector service to raise an exception
    mock_vector_service = MagicMock()
    mock_vector_service.index_chunks.side_effect = RuntimeError("Qdrant index write failure: disk full")

    custom_worker = IngestionWorkerService(
        session_factory=lambda: db_session,
        vector_service=mock_vector_service,
    )

    custom_worker.process_job(
        job_id="job_err_vector",
        document_id="doc_err_vector",
        content=pdf_bytes,
        source_filename="budget_memo.pdf",
        metadata={"department": "Finance"},
        db=db_session,
    )

    # Refresh records
    db_session.refresh(job)
    db_session.refresh(doc)

    assert job.status == "failed"
    assert job.stage == "failed"
    assert "Qdrant index write failure" in (job.error_message or "")
    assert doc.status == "failed"


def test_job_not_found_returns_404(client: TestClient) -> None:
    """Verify querying an unknown job ID returns HTTP 404."""
    response = client.get("/api/v1/documents/jobs/job_unknown_9999")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"


def test_document_status_not_found_returns_404(client: TestClient) -> None:
    """Verify querying status for unknown document ID returns HTTP 404."""
    response = client.get("/api/v1/documents/doc_unknown_9999/status")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
