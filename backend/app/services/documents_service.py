"""Service layer for municipal document ingestion and vector retrieval."""

from app.schemas.documents import DocumentItem, DocumentListResponse


class DocumentsService:
    """Service handling municipal PDF document retrieval and vector chunk status."""

    def __init__(self) -> None:
        # In-memory storage for Stage 3; will be backed by Qdrant/PostgreSQL in later stages.
        self._documents: list[DocumentItem] = []

    def get_documents(self, limit: int = 50, offset: int = 0) -> DocumentListResponse:
        """Retrieve collection of ingested municipal documents.

        In Stage 3, this returns the initial (empty or registered) collection
        prior to full vector pipeline wiring.
        """
        paginated = self._documents[offset : offset + limit]
        return DocumentListResponse(
            items=paginated,
            total=len(self._documents),
        )


documents_service = DocumentsService()
