"""Vector store abstraction and Qdrant implementation.

Decouples the application and search services from the underlying vector database implementation.
"""

import logging
import time
import uuid
import warnings
from abc import ABC, abstractmethod
from typing import Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import (
    ApiException,
    ResponseHandlingException,
    UnexpectedResponse,
)

from app.core.config import settings
from app.ingestion.models import DocumentChunk
from app.search.models import VectorIndexResult, VectorSearchResult

logger = logging.getLogger(__name__)

# Fixed namespace UUID to deterministically map string chunk IDs to RFC 4122 UUIDs
OPENCITIZEN_CHUNK_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def chunk_id_to_point_id(chunk_id: str) -> str:
    """Deterministically convert a chunk identifier into a valid Qdrant UUID string."""
    try:
        # Check if already a valid UUID
        return str(uuid.UUID(chunk_id))
    except (ValueError, AttributeError):
        return str(uuid.uuid5(OPENCITIZEN_CHUNK_NAMESPACE, chunk_id))


class BaseVectorStore(ABC):
    """Abstract interface defining the contract for vector database backends."""

    @abstractmethod
    def ensure_collection(
        self, collection_name: str | None = None, dimension: int | None = None
    ) -> bool:
        """Verify or create the vector collection with specified dimension."""

    @abstractmethod
    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        collection_name: str | None = None,
    ) -> VectorIndexResult:
        """Store document chunks and their embedding vectors with preserved provenance."""

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
        collection_name: str | None = None,
    ) -> list[VectorSearchResult]:
        """Perform semantic nearest-neighbor search."""

    @abstractmethod
    def delete_document(
        self, document_id: str, collection_name: str | None = None
    ) -> int:
        """Remove all indexed chunks belonging to a document ID."""

    @abstractmethod
    def count(self, collection_name: str | None = None) -> int:
        """Count total vectors indexed in the collection."""


class QdrantVectorStore(BaseVectorStore):
    """Qdrant-backed implementation of BaseVectorStore.

    Supports remote Qdrant clusters, local Docker instances, or hermetic
    in-memory storage for testing and offline execution.
    """

    def __init__(
        self,
        client: QdrantClient | None = None,
        host: str | None = None,
        port: int | None = None,
        url: str | None = None,
        api_key: str | None = None,
        default_collection: str | None = None,
        dimension: int | None = None,
    ):
        self.default_collection = default_collection or settings.QDRANT_COLLECTION_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

        if client is not None:
            self.client = client
        elif settings.QDRANT_IN_MEMORY:
            self.client = QdrantClient(location=":memory:")
        elif url or settings.QDRANT_URL:
            target_url = url or settings.QDRANT_URL
            self.client = QdrantClient(
                url=target_url,
                api_key=api_key or settings.QDRANT_API_KEY,
            )
        else:
            target_host = host or settings.QDRANT_HOST
            target_port = port or settings.QDRANT_PORT
            self.client = QdrantClient(
                host=target_host,
                port=target_port,
                api_key=api_key or settings.QDRANT_API_KEY,
            )

    def _resolve_collection(self, collection_name: str | None) -> str:
        return collection_name or self.default_collection

    def ensure_collection(
        self, collection_name: str | None = None, dimension: int | None = None
    ) -> bool:
        """Ensure target Qdrant collection exists, creating it if needed."""
        col_name = self._resolve_collection(collection_name)
        dim = dimension or self.dimension

        try:
            if self.client.collection_exists(collection_name=col_name):
                return True

            self.client.create_collection(
                collection_name=col_name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=models.Distance.COSINE,
                ),
            )

            # Create payload index for document_id on remote/server Qdrant to optimize filtered queries
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                try:
                    self.client.create_payload_index(
                        collection_name=col_name,
                        field_name="document_id",
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                except (UnexpectedResponse, ValueError, RuntimeError, OSError) as e:
                    logger.debug("Optional payload index creation notice: %s", e)

            logger.info(
                "Created Qdrant collection '%s' (dim=%d, distance=COSINE)",
                col_name,
                dim,
            )
            return True
        except Exception as e:
            logger.error("Failed to ensure Qdrant collection '%s': %s", col_name, e)
            raise

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        collection_name: str | None = None,
    ) -> VectorIndexResult:
        """Index chunks with vectors into Qdrant, preserving all metadata."""
        start_time = time.perf_counter()
        col_name = self._resolve_collection(collection_name)

        if not chunks:
            return VectorIndexResult(
                indexed_count=0,
                collection_name=col_name,
                document_ids=[],
                duration_ms=0.0,
            )

        if len(chunks) != len(vectors):
            raise ValueError(
                f"Chunks count ({len(chunks)}) must match vectors count ({len(vectors)})"
            )

        # Ensure collection exists
        vector_dim = len(vectors[0])
        self.ensure_collection(col_name, dimension=vector_dim)

        # Assemble points with preserved metadata
        points: list[models.PointStruct] = []
        doc_ids_set: set[str] = set()

        for chunk, vector in zip(chunks, vectors):
            doc_ids_set.add(chunk.document_id)
            point_id = chunk_id_to_point_id(chunk.chunk_id)

            payload = {
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "page_number": chunk.page_number,
                "source_filename": chunk.source_filename,
                "original_text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "character_count": chunk.character_count,
                "word_count": chunk.word_count,
                "metadata": chunk.metadata,
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=col_name,
            points=points,
            wait=True,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return VectorIndexResult(
            indexed_count=len(points),
            collection_name=col_name,
            document_ids=sorted(doc_ids_set),
            duration_ms=round(duration_ms, 2),
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
        collection_name: str | None = None,
    ) -> list[VectorSearchResult]:
        """Query Qdrant for semantically closest chunks, preserving metadata."""
        col_name = self._resolve_collection(collection_name)

        # If collection does not exist or vector database is unreachable, return empty results gracefully
        try:
            if not self.client.collection_exists(collection_name=col_name):
                return []
        except (
            UnexpectedResponse,
            ResponseHandlingException,
            ApiException,
            OSError,
            RuntimeError,
            ValueError,
        ) as e:
            logger.warning("Vector store unreachable or collection missing: %s", e)
            return []

        # Construct optional filter
        query_filter: models.Filter | None = None
        if filter_document_id:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=filter_document_id),
                    )
                ]
            )

        try:
            query_result = self.client.query_points(
                collection_name=col_name,
                query=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            )
        except (
            UnexpectedResponse,
            ResponseHandlingException,
            ApiException,
            OSError,
            RuntimeError,
            ValueError,
        ) as e:
            logger.error("Qdrant search error: %s", e)
            return []

        results: list[VectorSearchResult] = []
        for point in query_result.points:
            payload: dict[str, Any] = point.payload or {}
            results.append(
                VectorSearchResult(
                    chunk_id=payload.get("chunk_id", str(point.id)),
                    document_id=payload.get("document_id", ""),
                    page_number=int(payload.get("page_number", 1)),
                    source_filename=payload.get("source_filename", ""),
                    original_text=payload.get("original_text", payload.get("text", "")),
                    score=float(point.score),
                    metadata=payload.get("metadata", {}),
                )
            )

        return results

    def delete_document(
        self, document_id: str, collection_name: str | None = None
    ) -> int:
        """Delete all points associated with a specific document ID."""
        col_name = self._resolve_collection(collection_name)
        if not self.client.collection_exists(collection_name=col_name):
            return 0

        pre_count = self.count(col_name)

        delete_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                )
            ]
        )

        self.client.delete(
            collection_name=col_name,
            points_selector=models.FilterSelector(filter=delete_filter),
            wait=True,
        )

        post_count = self.count(col_name)
        return max(0, pre_count - post_count)

    def count(self, collection_name: str | None = None) -> int:
        """Count total vectors indexed in collection."""
        col_name = self._resolve_collection(collection_name)
        if not self.client.collection_exists(collection_name=col_name):
            return 0
        return self.client.count(collection_name=col_name).count
