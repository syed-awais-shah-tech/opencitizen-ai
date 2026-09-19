"""High-level Vector Search Service coordinating embedding providers and vector stores.

Shields the application from vector store and embedding implementation details,
enforcing the pipeline:
document chunks -> embedding generation -> vector collection -> vectors + metadata.
"""

import logging
from collections.abc import Sequence

from app.core.config import settings
from app.ingestion.models import DocumentChunk
from app.search.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.search.models import VectorIndexResult, VectorSearchResult
from app.search.vector_store import BaseVectorStore, QdrantVectorStore

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Coordinates embedding generation and vector database operations."""

    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        collection_name: str | None = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store or QdrantVectorStore(
            dimension=self.embedding_provider.dimension,
            default_collection=collection_name or settings.QDRANT_COLLECTION_NAME,
        )
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME

    def index_chunks(
        self,
        chunks: Sequence[DocumentChunk],
    ) -> VectorIndexResult:
        """Execute the ingestion-to-vector indexing pipeline:

        document chunks -> embedding generation -> vector store -> vectors + metadata
        """
        chunk_list = list(chunks)
        if not chunk_list:
            return VectorIndexResult(
                indexed_count=0,
                collection_name=self.collection_name,
                document_ids=[],
                duration_ms=0.0,
            )

        logger.info(
            "Generating embeddings for %d chunks using provider '%s' (dim=%d)",
            len(chunk_list),
            self.embedding_provider.model_name,
            self.embedding_provider.dimension,
        )

        texts = [chunk.text for chunk in chunk_list]
        vectors = self.embedding_provider.embed_batch(texts)

        return self.vector_store.index_chunks(
            chunks=chunk_list,
            vectors=vectors,
            collection_name=self.collection_name,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
    ) -> list[VectorSearchResult]:
        """Perform semantic search on indexed chunks using natural language query.

        Args:
            query: Natural language search string
            top_k: Number of most similar chunks to retrieve
            score_threshold: Optional minimum cosine similarity threshold
            filter_document_id: Optional document ID to filter provenance

        Returns:
            Ranked list of VectorSearchResult preserving all document metadata
        """
        if not query or not query.strip():
            return []

        query_vector = self.embedding_provider.embed_text(query.strip())

        return self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            filter_document_id=filter_document_id,
            collection_name=self.collection_name,
        )

    def delete_document(self, document_id: str) -> int:
        """Delete all chunk vectors associated with a document ID."""
        return self.vector_store.delete_document(
            document_id=document_id,
            collection_name=self.collection_name,
        )

    def count(self) -> int:
        """Return total number of vectors in the active collection."""
        return self.vector_store.count(collection_name=self.collection_name)
