"""Service layer for municipal document database operations."""

import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.documents import DocumentCreate, DocumentItem, DocumentListResponse


class DocumentsService:
    """Service handling municipal document metadata persistence and retrieval in PostgreSQL."""

    def get_documents(
        self, db: Session, limit: int = 50, offset: int = 0
    ) -> DocumentListResponse:
        """Retrieve paginated collection of municipal documents from database."""
        total_stmt = select(func.count()).select_from(Document)
        total = db.scalar(total_stmt) or 0

        stmt = (
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        documents = db.scalars(stmt).all()

        items = [
            DocumentItem(
                id=doc.id,
                title=doc.title,
                category=doc.category,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                size_bytes=doc.file_size_bytes,
                status=doc.status,  # type: ignore[arg-type]
                department=doc.department,
                summary=doc.summary or "",
                created_at=doc.created_at,
            )
            for doc in documents
        ]

        return DocumentListResponse(items=items, total=total)

    def get_document_by_id(self, db: Session, document_id: str) -> DocumentItem | None:
        """Retrieve single document by ID."""
        doc = db.get(Document, document_id)
        if not doc:
            return None
        return DocumentItem(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            size_bytes=doc.file_size_bytes,
            status=doc.status,  # type: ignore[arg-type]
            department=doc.department,
            summary=doc.summary or "",
            created_at=doc.created_at,
        )

    def create_document(self, db: Session, payload: DocumentCreate) -> DocumentItem:
        """Persist new document metadata in database."""
        doc = Document(
            id=f"doc_{uuid.uuid4().hex[:12]}",
            title=payload.title,
            department=payload.department,
            category=payload.category,
            page_count=payload.page_count,
            chunk_count=payload.chunk_count,
            file_size_bytes=payload.size_bytes,
            status="ready",
            summary=payload.summary,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        return DocumentItem(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            size_bytes=doc.file_size_bytes,
            status=doc.status,  # type: ignore[arg-type]
            department=doc.department,
            summary=doc.summary or "",
            created_at=doc.created_at,
        )


documents_service = DocumentsService()
