"""Asynchronous background worker service managing the document ingestion lifecycle.

Pipeline flow:
upload -> create processing job -> background worker -> extraction -> chunking -> embedding -> vector storage -> completed/failed
"""

from __future__ import annotations

import concurrent.futures
import logging
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.security import scrub_secrets
from app.db.session import SessionLocal
from app.ingestion.pipeline import PDFIngestionPipeline, pipeline as default_pdf_pipeline
from app.models.document import Document
from app.models.ingestion_job import IngestionJob
from app.search.dependencies import get_vector_search_service
from app.search.service import VectorSearchService

logger = logging.getLogger(__name__)


class IngestionWorkerService:
    """Orchestrates asynchronous document ingestion, chunking, embedding, and vector storage."""

    def __init__(
        self,
        pdf_pipeline: PDFIngestionPipeline | None = None,
        vector_service: VectorSearchService | None = None,
        session_factory: Callable[[], Session] | None = None,
        max_workers: int = 4,
    ) -> None:
        self._pdf_pipeline = pdf_pipeline
        self._vector_service = vector_service
        self._session_factory = session_factory or SessionLocal
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="ingestion_worker_"
        )

    @property
    def pdf_pipeline(self) -> PDFIngestionPipeline:
        if self._pdf_pipeline is None:
            return default_pdf_pipeline
        return self._pdf_pipeline

    @property
    def vector_service(self) -> VectorSearchService:
        if self._vector_service is None:
            return get_vector_search_service()
        return self._vector_service

    def set_session_factory(self, factory: Callable[[], Session]) -> None:
        """Allow setting custom session factory for testing environments."""
        self._session_factory = factory

    def create_job(self, db: Session, document_id: str) -> IngestionJob:
        """Initialize and persist a new processing job with status 'queued'."""
        job = IngestionJob(
            id=f"job_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            status="queued",
            stage="queued",
            progress_pct=0,
            total_pages=0,
            processed_pages=0,
            total_chunks=0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def get_job(self, db: Session, job_id: str) -> IngestionJob | None:
        """Retrieve a specific ingestion job by its unique identifier."""
        return db.get(IngestionJob, job_id)

    def get_document_jobs(self, db: Session, document_id: str) -> list[IngestionJob]:
        """Retrieve all historical or active jobs for a given document."""
        return (
            db.query(IngestionJob)
            .filter(IngestionJob.document_id == document_id)
            .order_by(IngestionJob.created_at.desc())
            .all()
        )

    def dispatch_job(
        self,
        job_id: str,
        document_id: str,
        content: bytes,
        source_filename: str,
        metadata: dict[str, Any] | None = None,
        sync: bool = False,
        db: Session | None = None,
    ) -> None:
        """Dispatch job execution either synchronously or asynchronously via thread pool.

        When sync=False (default for non-blocking HTTP requests), the worker executes
        in the background without delaying the HTTP response.
        """
        meta = metadata or {}
        if sync:
            self.process_job(
                job_id=job_id,
                document_id=document_id,
                content=content,
                source_filename=source_filename,
                metadata=meta,
                db=db,
            )
        else:
            self._executor.submit(
                self.process_job,
                job_id,
                document_id,
                content,
                source_filename,
                meta,
                None,
            )

    def process_job(
        self,
        job_id: str,
        document_id: str,
        content: bytes,
        source_filename: str,
        metadata: dict[str, Any],
        db: Session | None = None,
    ) -> None:
        """Execute the end-to-end ingestion pipeline:

        queued -> extraction -> chunking -> embedding -> vector_storage -> completed / failed
        """
        start_time = time.perf_counter()
        owns_session = db is None
        session: Session = self._session_factory() if owns_session else db  # type: ignore[assignment]

        try:
            job = session.get(IngestionJob, job_id)
            doc = session.get(Document, document_id)
            if not job or not doc:
                logger.error("Job '%s' or Document '%s' not found for processing.", job_id, document_id)
                return

            logger.info("IngestionWorker starting processing for job %s (document %s)", job_id, document_id)

            # Step 1: Extraction stage
            job.status = "processing"
            job.stage = "extraction"
            job.progress_pct = 20
            doc.status = "processing"
            session.commit()

            extracted_pages = self.pdf_pipeline.extractor.extract_from_bytes(content)
            valid_pages = [p for p in extracted_pages if not p.is_empty]
            warnings: list[str] = [
                f"Page {p.page_number} contained little or no text." for p in extracted_pages if p.is_empty
            ]

            # Step 2: Chunking stage
            job.stage = "chunking"
            job.progress_pct = 45
            job.total_pages = len(extracted_pages)
            job.processed_pages = len(valid_pages)
            session.commit()

            chunks = self.pdf_pipeline.chunker.chunk_pages(
                pages=valid_pages,
                document_id=document_id,
                source_filename=source_filename,
                base_metadata=metadata,
            )

            # Step 3: Embedding stage
            job.stage = "embedding"
            job.progress_pct = 70
            job.total_chunks = len(chunks)
            session.commit()

            # Step 4: Vector Storage stage (indexes into both dense Qdrant vector store and BM25 index)
            job.stage = "vector_storage"
            job.progress_pct = 85
            session.commit()

            self.vector_service.index_chunks(chunks)

            # Step 5: Completed stage
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            job.status = "completed"
            job.stage = "completed"
            job.progress_pct = 100
            job.processing_time_ms = elapsed_ms
            job.completed_at = datetime.now(timezone.utc)

            doc.status = "completed"
            doc.page_count = len(extracted_pages)
            doc.chunk_count = len(chunks)
            session.commit()

            logger.info(
                "IngestionWorker completed job %s in %.2fms: %d pages, %d chunks indexed.",
                job_id,
                elapsed_ms,
                len(extracted_pages),
                len(chunks),
            )

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_msg = scrub_secrets(str(exc))
            logger.error("IngestionWorker encountered error on job %s: %s", job_id, error_msg, exc_info=True)

            session.rollback()
            try:
                job = session.get(IngestionJob, job_id)
                doc = session.get(Document, document_id)
                if job:
                    job.status = "failed"
                    job.stage = "failed"
                    job.error_message = error_msg
                    job.processing_time_ms = elapsed_ms
                    job.completed_at = datetime.now(timezone.utc)
                if doc:
                    doc.status = "failed"
                session.commit()
            except Exception as commit_err:
                logger.error("Failed to commit failure state for job %s: %s", job_id, commit_err)
        finally:
            if owns_session:
                session.close()


ingestion_worker = IngestionWorkerService()
