"""Dependency providers and singletons for search components."""

from functools import lru_cache

from app.search.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.search.lexical import BM25Index
from app.search.reranker import ReciprocalRankFusionReranker
from app.search.service import VectorSearchService
from app.search.vector_store import BaseVectorStore, QdrantVectorStore


@lru_cache
def get_embedding_provider_instance() -> BaseEmbeddingProvider:
    """Cached singleton embedding provider instance."""
    return get_embedding_provider()


@lru_cache
def get_vector_store_instance() -> BaseVectorStore:
    """Cached singleton vector store instance."""
    provider = get_embedding_provider_instance()
    return QdrantVectorStore(dimension=provider.dimension)


@lru_cache
def get_bm25_index_instance() -> BM25Index:
    """Cached singleton BM25 lexical index instance."""
    return BM25Index()


@lru_cache
def get_reranker_instance() -> ReciprocalRankFusionReranker:
    """Cached singleton Reciprocal Rank Fusion reranker instance."""
    return ReciprocalRankFusionReranker()


def get_vector_search_service() -> VectorSearchService:
    """Provide VectorSearchService instance with configured dependencies."""
    provider = get_embedding_provider_instance()
    store = get_vector_store_instance()
    lexical_index = get_bm25_index_instance()
    reranker = get_reranker_instance()
    return VectorSearchService(
        vector_store=store,
        embedding_provider=provider,
        lexical_index=lexical_index,
        reranker=reranker,
    )
