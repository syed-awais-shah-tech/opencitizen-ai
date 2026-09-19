"""OpenCitizen AI search and vector retrieval module."""

from app.search.embeddings import (
    BaseEmbeddingProvider,
    DeterministicEmbeddingProvider,
    get_embedding_provider,
)
from app.search.models import (
    SearchQuery,
    VectorIndexResult,
    VectorSearchResult,
)
from app.search.service import VectorSearchService
from app.search.vector_store import (
    BaseVectorStore,
    QdrantVectorStore,
)

__all__ = [
    "BaseEmbeddingProvider",
    "BaseVectorStore",
    "DeterministicEmbeddingProvider",
    "QdrantVectorStore",
    "SearchQuery",
    "VectorIndexResult",
    "VectorSearchResult",
    "VectorSearchService",
    "get_embedding_provider",
]
