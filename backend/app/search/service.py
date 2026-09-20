"""High-level Vector Search Service coordinating embedding providers, vector stores,
lexical BM25 indexing, and Reciprocal Rank Fusion (RRF) reranking.

Shields the application from vector store and embedding implementation details,
enforcing the pipeline:
document chunks -> embedding generation -> vector collection -> vectors + metadata
while also maintaining the lexical inverted index for hybrid keyword retrieval.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Literal

from app.core.config import settings
from app.ingestion.models import DocumentChunk
from app.search.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.search.lexical import BM25Index
from app.search.models import VectorIndexResult, VectorSearchResult
from app.search.reranker import ReciprocalRankFusionReranker
from app.search.vector_store import BaseVectorStore, QdrantVectorStore

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Coordinates embedding generation, vector database operations, BM25 lexical indexing,

    and reciprocal rank fusion reranking.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        collection_name: str | None = None,
        lexical_index: BM25Index | None = None,
        reranker: ReciprocalRankFusionReranker | None = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store or QdrantVectorStore(
            dimension=self.embedding_provider.dimension,
            default_collection=collection_name or settings.QDRANT_COLLECTION_NAME,
        )
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.lexical_index = lexical_index if lexical_index is not None else BM25Index()
        self.reranker = (
            reranker if reranker is not None else ReciprocalRankFusionReranker()
        )

    def index_chunks(
        self,
        chunks: Sequence[DocumentChunk],
    ) -> VectorIndexResult:
        """Execute the ingestion indexing pipeline for both semantic vectors and lexical BM25:

        document chunks -> embedding generation -> vector store -> vectors + metadata
                        -> BM25 inverted index
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
            "Indexing %d chunks into BM25 index and vector store '%s' (dim=%d)",
            len(chunk_list),
            self.collection_name,
            self.embedding_provider.dimension,
        )

        # Index in BM25 lexical index
        self.lexical_index.index_chunks(chunk_list)

        # Generate dense embeddings
        texts = [chunk.text for chunk in chunk_list]
        vectors = self.embedding_provider.embed_batch(texts)

        # Index in vector store
        return self.vector_store.index_chunks(
            chunks=chunk_list,
            vectors=vectors,
            collection_name=self.collection_name,
        )

    def search_semantic(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
    ) -> list[VectorSearchResult]:
        """Perform dense semantic search on indexed chunks using natural language query.

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

    def search_lexical(
        self,
        query: str,
        top_k: int = 5,
        filter_document_id: str | None = None,
    ) -> list[VectorSearchResult]:
        """Perform lexical (keyword-based) BM25 retrieval over indexed chunks.

        Args:
            query: Keyword query string (alphanumerics, IDs, names)
            top_k: Number of most matching chunks to retrieve
            filter_document_id: Optional document ID to filter provenance

        Returns:
            Ranked list of VectorSearchResult with BM25 scores
        """
        if not query or not query.strip():
            return []

        return self.lexical_index.search(
            query=query.strip(),
            top_k=top_k,
            filter_document_id=filter_document_id,
        )

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
        candidate_pool_multiplier: int = 3,
    ) -> list[VectorSearchResult]:
        """Perform hybrid retrieval combining semantic vector search and BM25 lexical search,

        fused and reranked using Reciprocal Rank Fusion (RRF).

        Args:
            query: Natural language or keyword query
            top_k: Number of reranked results to return
            score_threshold: Optional calibrated score threshold
            filter_document_id: Optional document ID filter
            candidate_pool_multiplier: Multiplier for initial candidate retrieval pool

        Returns:
            Ranked list of VectorSearchResult fused with provenance metadata
        """
        if not query or not query.strip():
            return []

        pool_k = max(top_k * candidate_pool_multiplier, 10)

        semantic_candidates = self.search_semantic(
            query=query,
            top_k=pool_k,
            score_threshold=None,
            filter_document_id=filter_document_id,
        )

        lexical_candidates = self.search_lexical(
            query=query,
            top_k=pool_k,
            filter_document_id=filter_document_id,
        )

        return self.reranker.rerank(
            semantic_results=semantic_candidates,
            lexical_results=lexical_candidates,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
        mode: Literal["hybrid", "semantic", "lexical"] | str = "hybrid",
    ) -> list[VectorSearchResult]:
        """Search indexed document chunks using hybrid, semantic, or lexical retrieval.

        Defaults to 'hybrid' retrieval combining semantic vector search and BM25 keyword search.

        Args:
            query: Search query string
            top_k: Number of most similar chunks to retrieve
            score_threshold: Optional minimum relevance score threshold
            filter_document_id: Optional document ID to filter provenance
            mode: Retrieval mode ('hybrid', 'semantic', or 'lexical')

        Returns:
            Ranked list of VectorSearchResult preserving all document metadata
        """
        if not query or not query.strip():
            return []

        if mode == "semantic":
            return self.search_semantic(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                filter_document_id=filter_document_id,
            )
        elif mode == "lexical":
            return self.search_lexical(
                query=query,
                top_k=top_k,
                filter_document_id=filter_document_id,
            )
        else:
            return self.search_hybrid(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                filter_document_id=filter_document_id,
            )

    def delete_document(self, document_id: str) -> int:
        """Delete all chunk vectors and lexical entries associated with a document ID."""
        self.lexical_index.delete_document(document_id)
        return self.vector_store.delete_document(
            document_id=document_id,
            collection_name=self.collection_name,
        )

    def count(self) -> int:
        """Return total number of vectors in the active collection."""
        return self.vector_store.count(collection_name=self.collection_name)
