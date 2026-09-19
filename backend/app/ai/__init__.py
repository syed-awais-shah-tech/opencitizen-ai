"""AI provider and context management module for OpenCitizen."""

from app.ai.models import EvidenceContext, LLMAnswer
from app.ai.prompts import (
    INSUFFICIENT_EVIDENCE_PHRASE,
    OPENCITIZEN_SYSTEM_INSTRUCTION,
    build_rag_prompt,
)
from app.ai.provider import (
    BaseAIProvider,
    GeminiProvider,
    MockAIProvider,
    get_ai_provider,
)

__all__ = [
    "INSUFFICIENT_EVIDENCE_PHRASE",
    "OPENCITIZEN_SYSTEM_INSTRUCTION",
    "BaseAIProvider",
    "EvidenceContext",
    "GeminiProvider",
    "LLMAnswer",
    "MockAIProvider",
    "build_rag_prompt",
    "get_ai_provider",
]
