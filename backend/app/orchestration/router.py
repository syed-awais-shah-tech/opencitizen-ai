"""Controlled query router determining optimal routing category for incoming inquiries.

Categorizes inquiries into:
1. document_retrieval (Qdrant semantic search)
2. data_analysis (DuckDB structured aggregation)
3. both (Hybrid: DuckDB calculations + Qdrant qualitative context)
4. unsupported (Off-topic, chitchat, or ungroundable requests)
"""

import json
import logging
import re
from typing import Any

from app.ai.provider import BaseAIProvider, GeminiProvider, get_ai_provider
from app.orchestration.models import RouteCategory, RoutingDecision

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_INSTRUCTION = """You are the OpenCitizen AI Query Router.
Your role is to analyze a citizen or researcher's inquiry and classify it into EXACTLY ONE of four routing categories:

1. "document_retrieval"
   - Use when the question asks about narrative text, policy descriptions, statements, or qualitative explanations found in documents/reports.
   - Example: "What does the report say about employment?"

2. "data_analysis"
   - Use when the question asks for numerical calculations, sums, averages, counts, minimum, maximum, rankings, or structured tabular data filtering.
   - Example: "Which province has the highest unemployment?"

3. "both"
   - Use when the question requires BOTH a quantitative calculation/metric AND a qualitative narrative explanation from reports (e.g. asking "why" a metric is higher/lower according to a document).
   - Example: "Why is unemployment higher in province X according to the report?"

4. "unsupported"
   - Use when the question is conversational chitchat (e.g. greetings, jokes), completely off-topic (e.g. weather, recipes), or outside the scope of municipal civic documents and structured datasets.
   - Example: "Tell me a joke" or "What is the capital of France?"

SECURITY INVARIANT:
You do NOT execute database queries or SQL. You ONLY classify intent.

Respond strictly in valid JSON matching this schema:
{
  "route": "document_retrieval" | "data_analysis" | "both" | "unsupported",
  "reasoning": "Brief explanation of the routing choice.",
  "confidence": 0.95,
  "target_table": "optional_table_name_or_null",
  "search_query": "optional_search_query_or_null"
}
"""


class QueryRouter:
    """Classifies natural language inquiries into validated routing paths."""

    def __init__(self, ai_provider: BaseAIProvider | None = None) -> None:
        self.ai_provider = ai_provider or get_ai_provider()

    def classify(self, question: str) -> RoutingDecision:
        """Classify question into one of the 4 routing categories.

        Uses Gemini if configured and reachable; reliably falls back to
        deterministic semantic pattern matching in offline/mock environments.
        """
        clean_q = question.strip()
        if not clean_q:
            return RoutingDecision(
                route=RouteCategory.UNSUPPORTED,
                reasoning="Empty query provided.",
                confidence=1.0,
                suggested_tools=[],
            )

        # 1. Attempt AI model routing if GeminiProvider is active
        if isinstance(self.ai_provider, GeminiProvider):
            try:
                ai_decision = self._classify_with_model(clean_q)
                if ai_decision is not None:
                    return ai_decision
            except Exception as exc:
                logger.warning(
                    "Model-based routing encountered an issue: %s. Falling back to rule-based routing.",
                    exc,
                )

        # 2. Deterministic rule-based classification (always reliable and hermetic)
        return self.rule_based_classify(clean_q)

    def _classify_with_model(self, question: str) -> RoutingDecision | None:
        """Query Gemini model for controlled classification output."""
        prompt = (
            f"Inquiry to classify:\n\"{question}\"\n\n"
            "Classify this inquiry into document_retrieval, data_analysis, both, or unsupported. "
            "Output JSON only."
        )
        response_text = self.ai_provider.generate_text(
            prompt=prompt,
            system_instruction=ROUTER_SYSTEM_INSTRUCTION,
        )

        # Extract JSON from response
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not match:
            return None

        data = json.loads(match.group(0))
        raw_route = str(data.get("route", "")).strip().lower()

        try:
            route_enum = RouteCategory(raw_route)
        except ValueError:
            return None

        tools = self._get_tools_for_route(route_enum)
        return RoutingDecision(
            route=route_enum,
            reasoning=data.get("reasoning", "Classified by Gemini AI Router."),
            confidence=float(data.get("confidence", 0.9)),
            target_table=data.get("target_table"),
            search_query=data.get("search_query") or question,
            suggested_tools=tools,
        )

    def rule_based_classify(self, question: str) -> RoutingDecision:
        """Deterministic semantic classifier covering all four routing categories."""
        q = question.lower().strip()

        # ----------------------------------------------------------------------
        # Category 4: Unsupported / Neither / Out of Scope
        # ----------------------------------------------------------------------
        unsupported_patterns = [
            r"^(hello|hi|hey|greetings|good\s+morning|good\s+afternoon)\b",
            r"\b(joke|riddle|funny|chitchat)\b",
            r"\b(weather|forecast|temperature)\b",
            r"\b(recipe|bake|cooking|ingredients)\b",
            r"\b(capital of|population of mars|who won the super bowl)\b",
            r"\b(write a python script|write code|hack|jailbreak)\b",
            r"\b(play music|sing a song|tell me a story)\b",
        ]
        if any(re.search(pat, q) for pat in unsupported_patterns):
            # Check if there are civic terms overriding chitchat
            civic_override = any(
                w in q for w in ("report", "budget", "expense", "contract", "grant", "unemployment", "ordinance")
            )
            if not civic_override:
                return RoutingDecision(
                    route=RouteCategory.UNSUPPORTED,
                    reasoning="Inquiry is conversational, out-of-scope, or unrelated to verifiable municipal documents or structured datasets.",
                    confidence=0.98,
                    suggested_tools=[],
                )

        # ----------------------------------------------------------------------
        # Markers for Analytical Data vs. Narrative Document Retrieval
        # ----------------------------------------------------------------------
        # Narrative markers: asking for explanations, reasons, or statements from documents
        narrative_markers = [
            "report", "document", "pdf", "memo", "policy", "statement", "notes",
            "why", "reason", "reasons", "explain why", "according to",
            "what does the report say", "mentioned in the report", "audit notes",
            "section", "chapter", "guideline", "stated in",
        ]
        has_narrative = any(m in q for m in narrative_markers)

        # Quantitative/analytical markers: calculations, numbers, metrics, aggregations
        analytical_markers = [
            "highest", "lowest", "maximum", "minimum", "max", "min", "most", "least",
            "total", "sum", "average", "avg", "mean", "count", "how many",
            "unemployment", "rate", "cost", "spending", "spent", "amount", "expense", "expenses",
            "allocated", "disbursed", "grant amount", "contract value", "values",
            "which province", "which department", "which vendor",
            "rank", "fewer than", "greater than", "more than", "higher", "lower", "increase", "decrease",
        ]
        has_analytical = any(m in q for m in analytical_markers)

        # Table detection
        target_table = None
        if any(w in q for w in ("unemployment", "labor", "province", "jobless")):
            target_table = "regional_unemployment"
        elif any(w in q for w in ("expense", "spent", "spending", "department")):
            target_table = "dept_expenses"
        elif any(w in q for w in ("contract", "vendor", "contractor", "award")):
            target_table = "vendor_contracts"
        elif any(w in q for w in ("grant", "recipient", "disbursed", "cultural fund")):
            target_table = "civic_grants"

        # ----------------------------------------------------------------------
        # Category 3: Both (Hybrid: Quantitative Calculation + Qualitative Narrative)
        # e.g. "Why is unemployment higher in province X according to the report?"
        # ----------------------------------------------------------------------
        is_hybrid_attribution = (
            ("why" in q or "reason" in q or "explain" in q or "according to" in q)
            and ("report" in q or "document" in q or "notes" in q)
            and has_analytical
        )

        if is_hybrid_attribution:
            return RoutingDecision(
                route=RouteCategory.BOTH,
                reasoning=(
                    "Inquiry requires structured quantitative analysis to identify the metric "
                    "combined with qualitative document retrieval to extract narrative explanations from reports."
                ),
                confidence=0.95,
                target_table=target_table,
                search_query=question,
                suggested_tools=["data_analysis", "document_retrieval"],
            )

        # ----------------------------------------------------------------------
        # Category 2: Data Analysis (DuckDB)
        # e.g. "Which province has the highest unemployment?"
        # ----------------------------------------------------------------------
        # If it has strong analytical markers and doesn't ask to read/explain text from a report
        is_pure_analysis = (
            has_analytical
            and not (
                "what does the report say" in q
                or "according to the report" in q
                or ("report" in q and not any(w in q for w in ("highest", "lowest", "sum", "total", "average", "which province", "count")))
            )
        )

        if is_pure_analysis:
            return RoutingDecision(
                route=RouteCategory.DATA_ANALYSIS,
                reasoning="Inquiry asks for structured statistical aggregations, ranking, or filtering over tabular municipal datasets.",
                confidence=0.92,
                target_table=target_table,
                suggested_tools=["data_analysis"],
            )

        # ----------------------------------------------------------------------
        # Category 1: Document Retrieval (Qdrant)
        # e.g. "What does the report say about employment?"
        # ----------------------------------------------------------------------
        if has_narrative or any(w in q for w in ("what", "how", "who", "when", "describe", "outline")):
            return RoutingDecision(
                route=RouteCategory.DOCUMENT_RETRIEVAL,
                reasoning="Inquiry asks for qualitative text excerpts, policy context, or statements from indexed municipal documents.",
                confidence=0.88,
                search_query=question,
                suggested_tools=["document_retrieval"],
            )

        # Default fallback: unsupported if totally unrecognized
        return RoutingDecision(
            route=RouteCategory.UNSUPPORTED,
            reasoning="Inquiry cannot be mapped to available civic documents or structured datasets.",
            confidence=0.75,
            suggested_tools=[],
        )

    @staticmethod
    def _get_tools_for_route(route: RouteCategory) -> list[str]:
        """Map RouteCategory to explicit tool names."""
        if route == RouteCategory.DOCUMENT_RETRIEVAL:
            return ["document_retrieval"]
        if route == RouteCategory.DATA_ANALYSIS:
            return ["data_analysis"]
        if route == RouteCategory.BOTH:
            return ["data_analysis", "document_retrieval"]
        return []


# Global singleton router
query_router_service = QueryRouter()
