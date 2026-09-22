# Extending AI Providers: Adding LLM & Embedding Integrations

OpenCitizen AI decouples the reasoning and synthesis engine from vendor-specific SDKs using an abstract provider pattern (`BaseAIProvider` and `BaseEmbeddingProvider`).

This design allows you to add support for local models (e.g. Ollama, vLLM, Llama.cpp) or other commercial API providers (e.g. Anthropic Claude, OpenAI, Cohere) without modifying core RAG pipelines.

---

## 1. Core Invariants for AI Providers

Every AI provider implementation must uphold OpenCitizen AI's core evidence-grounding invariants:

1. **Strict Evidence Grounding**: The model must synthesize answers **only** from the supplied evidence chunks.
2. **Attribution & Citations**: The synthesized answer must cite the source documents and page numbers.
3. **Explicit Insufficient Evidence**: If the retrieved evidence does not contain sufficient facts to answer the question, the provider must explicitly state that the evidence is insufficient. It must **never** hallucinate facts from parametric memory.
4. **No Secrets in Logs**: API keys must be loaded via `pydantic-settings` and never logged or serialized.

---

## 2. Implementing a Generative AI Provider

All generative AI providers implement the `BaseAIProvider` abstract class defined in `backend/app/ai/provider.py`:

```python
class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name or identifier of the underlying generative model."""

    @abstractmethod
    def generate_grounded_answer(
        self,
        question: str,
        contexts: list[EvidenceContext],
    ) -> LLMAnswer:
        """Generate an answer strictly grounded in the supplied evidence contexts."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """Generate open text from a prompt and optional system instructions."""
```

### Example: Adding an Anthropic Claude Provider

Create `backend/app/ai/anthropic_provider.py`:

```python
"""Anthropic Claude AI provider implementation."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.models import EvidenceContext, LLMAnswer
from app.ai.prompts import (
    INSUFFICIENT_EVIDENCE_PHRASE,
    OPENCITIZEN_SYSTEM_INSTRUCTION,
    build_rag_prompt,
)
from app.ai.provider import BaseAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider implementing BaseAIProvider."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022"):
        self._api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None)
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY is required to initialize AnthropicProvider.")
        self._model = model

        import anthropic
        self._client = anthropic.Anthropic(api_key=self._api_key)

    @property
    def model_name(self) -> str:
        return self._model

    def generate_grounded_answer(
        self,
        question: str,
        contexts: list[EvidenceContext],
    ) -> LLMAnswer:
        if not contexts:
            return LLMAnswer(
                answer_text=INSUFFICIENT_EVIDENCE_PHRASE,
                is_grounded=True,
                is_insufficient_evidence=True,
                model_name=self._model,
                citation_references=[],
            )

        prompt = build_rag_prompt(question, contexts)
        response_text = self.generate_text(
            prompt=prompt,
            system_instruction=OPENCITIZEN_SYSTEM_INSTRUCTION,
        )

        is_insufficient = (
            INSUFFICIENT_EVIDENCE_PHRASE.lower() in response_text.lower()
            or "insufficient evidence" in response_text.lower()
        )

        cited_sources = [
            ctx.document_title
            for ctx in contexts
            if ctx.document_title.lower() in response_text.lower()
        ]

        return LLMAnswer(
            answer_text=response_text,
            is_grounded=True,
            is_insufficient_evidence=is_insufficient,
            model_name=self._model,
            citation_references=cited_sources,
        )

    def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            temperature=0.2,
            system=system_instruction or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text if message.content else ""
```

---

## 3. Implementing an Embedding Provider

All embedding providers implement `BaseEmbeddingProvider` in `backend/app/search/embeddings.py`:

```python
class BaseEmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality (e.g. 768, 1536)."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate dense vector embedding for single text snippet."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding generation."""
```

### Example: Adding a Local HuggingFace / Sentence-Transformers Provider

```python
from sentence_transformers import SentenceTransformer
from app.search.embeddings import BaseEmbeddingProvider


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts).tolist()
```

---

## 4. Registering Providers in Factory Functions

Update `get_ai_provider()` in `backend/app/ai/provider.py`:
```python
if resolved_type == "anthropic":
    return AnthropicProvider(api_key=resolved_key, model=resolved_model)
```

And update `get_embedding_provider()` in `backend/app/search/embeddings.py` accordingly.

---

## 5. Testing Your Provider

1. Write mock/offline tests to ensure your provider correctly handles:
   - Empty contexts list -> Returns `INSUFFICIENT_EVIDENCE_PHRASE`.
   - Populated evidence -> Extracts source titles into `citation_references`.
   - Error responses from upstream API -> Gracefully raises an `AppException`.
2. Add provider configuration fields to `backend/app/core/config.py`.
3. Verify that `pytest backend/tests/test_rag_pipeline.py` passes.
