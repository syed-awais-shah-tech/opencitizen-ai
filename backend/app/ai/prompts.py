"""System prompts, grounding guidelines, and context templates for RAG."""

from app.ai.models import EvidenceContext

INSUFFICIENT_EVIDENCE_PHRASE = (
    "The available evidence is insufficient to answer this question."
)

OPENCITIZEN_SYSTEM_INSTRUCTION = f"""You are OpenCitizen AI, an evidence-grounded civic intelligence assistant.
Your task is to answer the user's question using ONLY the retrieved document evidence provided in the prompt.

CRITICAL GROUNDING RULES:
1. Ground all claims, statistics, financial figures, dates, and conclusions STRICTLY in the provided evidence.
2. If the provided evidence is empty, unrelated, or lacks enough information to answer the question truthfully and completely, you MUST state explicitly:
   "{INSUFFICIENT_EVIDENCE_PHRASE}"
   Do not guess, speculate, extrapolate, or bring in outside knowledge not present in the evidence.
3. Every factual claim must be accompanied by an inline source reference in the exact format:
   [Source: <filename>, Page: <page_number>]
4. NEVER fabricate, hallucinate, or assume citations, document titles, page numbers, or facts.
5. Preserve source filenames and page numbers accurately without alteration.
"""


def build_rag_prompt(question: str, contexts: list[EvidenceContext]) -> str:
    """Format user question and retrieved evidence chunks into structured RAG prompt."""
    if not contexts:
        return f"""USER QUESTION:
{question}

RETRIEVED EVIDENCE:
No relevant document evidence was found in the database.
"""

    evidence_sections: list[str] = []
    for idx, ctx in enumerate(contexts, start=1):
        section = (
            f"--- EVIDENCE EXCERPT [{idx}] ---\n"
            f"Source File: {ctx.document_title}\n"
            f"Page Number: {ctx.page_number}\n"
            f"Chunk ID: {ctx.chunk_id}\n"
            f"Excerpt Content:\n"
            f"{ctx.text.strip()}\n"
            f"---------------------------------"
        )
        evidence_sections.append(section)

    evidence_text = "\n\n".join(evidence_sections)

    return f"""RETRIEVED EVIDENCE:
{evidence_text}

USER QUESTION:
{question}

INSTRUCTIONS:
Answer the question above based strictly on the retrieved evidence excerpts provided.
Include inline citations referencing [Source: <filename>, Page: <page_number>].
If the evidence does not contain the answer, reply with:
"{INSUFFICIENT_EVIDENCE_PHRASE}"
"""
