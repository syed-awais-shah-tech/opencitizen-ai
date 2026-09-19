"""AI provider abstraction and implementations for Gemini and offline test execution.

Shields the application and RAG pipelines from Gemini SDK details,
enforcing strict evidence grounding contracts.
"""

import logging
import re
from abc import ABC, abstractmethod

from app.ai.models import EvidenceContext, LLMAnswer
from app.ai.prompts import (
    INSUFFICIENT_EVIDENCE_PHRASE,
    OPENCITIZEN_SYSTEM_INSTRUCTION,
    build_rag_prompt,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Abstract interface defining the contract for AI/LLM providers."""

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


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider utilizing official google-genai SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self._api_key = api_key or settings.GEMINI_API_KEY
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY is required to initialize GeminiProvider. "
                "Ensure it is set in environment or settings."
            )
        self._model = model or settings.GEMINI_MODEL

        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        except ImportError as exc:
            raise ImportError(
                "google-genai is required for GeminiProvider. "
                "Install it via 'pip install google-genai'."
            ) from exc

    @property
    def model_name(self) -> str:
        return self._model

    def generate_grounded_answer(
        self,
        question: str,
        contexts: list[EvidenceContext],
    ) -> LLMAnswer:
        """Synthesize answer using Gemini with strict system instruction grounding."""
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

        # Detect which documents were referenced
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

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """Issue prompt generation to Gemini client."""
        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=0.2,
                system_instruction=system_instruction,
            )

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            logger.error("Gemini content generation failed: %s", e)
            raise


class MockAIProvider(BaseAIProvider):
    """Deterministic, offline AI provider for hermetic testing and development.

    Synthesizes grounded answers strictly from supplied evidence,
    correctly cites sources, and asserts insufficient evidence when information is lacking.
    """

    def __init__(self, model_name: str = "mock-grounded-v1"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_grounded_answer(
        self,
        question: str,
        contexts: list[EvidenceContext],
    ) -> LLMAnswer:
        """Synthesize answer or return insufficient evidence based on context analysis."""
        if not contexts:
            return LLMAnswer(
                answer_text=INSUFFICIENT_EVIDENCE_PHRASE,
                is_grounded=True,
                is_insufficient_evidence=True,
                model_name=self._model_name,
                citation_references=[],
            )

        # Tokenize question terms to evaluate semantic relevance
        q_tokens = set(re.findall(r"\w{4,}", question.lower()))
        # Filter out common stop-words
        stop_words = {
            "what",
            "where",
            "when",
            "which",
            "could",
            "would",
            "should",
            "about",
            "there",
            "their",
            "total",
            "were",
            "been",
            "from",
            "with",
            "have",
        }
        substantive_tokens = q_tokens - stop_words

        matching_contexts: list[EvidenceContext] = []
        for ctx in contexts:
            ctx_lower = ctx.text.lower()
            if any(token in ctx_lower for token in substantive_tokens):
                matching_contexts.append(ctx)

        if not matching_contexts:
            # Evidence is unrelated or insufficient to answer the question
            return LLMAnswer(
                answer_text=INSUFFICIENT_EVIDENCE_PHRASE,
                is_grounded=True,
                is_insufficient_evidence=True,
                model_name=self._model_name,
                citation_references=[],
            )

        # Synthesize answer using the most relevant matching contexts
        primary_ctx = matching_contexts[0]
        cited_sources: list[str] = [primary_ctx.document_title]

        # Extract sentences from excerpt that match question tokens
        sentences = [
            s.strip()
            for s in re.split(r"[.!?]\s+", primary_ctx.text)
            if any(t in s.lower() for t in substantive_tokens)
        ]
        grounded_fact = sentences[0] if sentences else primary_ctx.text.strip()
        if not grounded_fact.endswith("."):
            grounded_fact += "."

        answer_text = (
            f"Based on municipal records: {grounded_fact} "
            f"[Source: {primary_ctx.document_title}, Page: {primary_ctx.page_number}]"
        )

        return LLMAnswer(
            answer_text=answer_text,
            is_grounded=True,
            is_insufficient_evidence=False,
            model_name=self._model_name,
            citation_references=cited_sources,
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """Return deterministic mock response."""
        return "Deterministic mock text response."


def get_ai_provider(
    provider_type: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> BaseAIProvider:
    """Factory function resolving configured AI provider."""
    resolved_type = (provider_type or settings.LLM_PROVIDER).lower()
    resolved_key = api_key or settings.GEMINI_API_KEY
    resolved_model = model or settings.GEMINI_MODEL

    # If Gemini explicitly requested or API key available and not set to mock
    if resolved_type == "gemini" or (resolved_key and resolved_type != "mock"):
        return GeminiProvider(api_key=resolved_key, model=resolved_model)

    return MockAIProvider()
