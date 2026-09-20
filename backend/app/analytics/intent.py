"""Intent extractor translating natural language questions into structured AnalysisPlan objects."""

import re
from typing import Any

from app.analytics.exceptions import AnalysisPlanValidationError
from app.analytics.schemas import AnalysisPlan, FilterCondition, OperationType, SortCondition


class IntentExtractor:
    """Translates natural language analytical questions into explicit, safe AnalysisPlan objects."""

    @classmethod
    def extract_plan(
        cls,
        question: str,
        table_name: str,
        table_schema: dict[str, str],
        default_limit: int = 100,
    ) -> AnalysisPlan:
        """Extract an AnalysisPlan from a natural language question and table schema.

        A natural language question is NEVER translated directly into raw unvalidated SQL.
        Instead, it resolves into an explicit AnalysisPlan intermediate representation.
        """
        q = question.lower().strip()
        available_columns = {k.lower(): v for k, v in table_schema.items()}

        # 1. Detect Operation
        operation: OperationType = cls._detect_operation(q)

        # 2. Resolve Target Column
        target_column = cls._resolve_target_column(q, operation, available_columns)

        # 3. Detect Grouping Columns
        group_by = cls._detect_group_by(q, available_columns)

        # 4. Detect Filter Constraints
        filters = cls._detect_filters(q, available_columns)

        # 5. Detect Sorting Directives
        sort_by = cls._detect_sorting(q, operation, target_column, group_by)

        # 6. Detect Limit / Top N
        limit = cls._detect_limit(q, default_limit)

        plan = AnalysisPlan(
            table_name=table_name,
            operation=operation,
            target_column=target_column,
            group_by=group_by,
            filters=filters,
            sort_by=sort_by,
            limit=limit,
        )

        return plan

    @classmethod
    def _detect_operation(cls, q: str) -> OperationType:
        """Identify operation type from linguistic markers."""
        if any(w in q for w in ("average", "avg", "mean")):
            return "average"
        if any(w in q for w in ("minimum", "min", "lowest", "least", "cheapest", "smallest")):
            return "minimum"
        if any(w in q for w in ("maximum", "max", "highest", "most", "largest", "biggest", "greatest")):
            return "maximum"
        if any(w in q for w in ("how many", "count", "number of", "count of")):
            return "count"
        if any(w in q for w in ("total", "sum", "spent", "expenditure", "combined", "allocated", "disbursed")):
            return "sum"

        # Default fallback operation
        return "count"

    @classmethod
    def _resolve_target_column(
        cls, q: str, operation: OperationType, schema: dict[str, str]
    ) -> str | None:
        """Determine target column matching operation requirements."""
        if operation == "count":
            # For count, check if a specific column is explicitly mentioned
            for col in schema:
                if f"count of {col}" in q or f"count {col}" in q:
                    return col
            return "*"

        numeric_cols = [col for col, dtype in schema.items() if dtype in ("INTEGER", "DOUBLE")]
        date_cols = [col for col, dtype in schema.items() if dtype == "DATE"]

        # 1. Exact or keyword column match in question
        for col in schema:
            col_tokens = col.replace("_", " ").split()
            if col in q or all(tok in q for tok in col_tokens):
                if operation in ("sum", "average") and col in numeric_cols:
                    return col
                if operation in ("minimum", "maximum"):
                    return col

        # 2. Semantic keywords mapping
        if "spent" in q or "amount" in q or "expense" in q or "expenditure" in q:
            for col in ("amount", "grant_amount", "spent_to_date", "total_spent"):
                if col in schema:
                    return col
        if "value" in q or "contract" in q:
            if "contract_value" in schema:
                return "contract_value"
        if "budget" in q or "allocated" in q:
            for col in ("budget_allocated", "budget", "amount"):
                if col in schema:
                    return col
        if "pct" in q or "completion" in q:
            if "completion_pct" in schema:
                return "completion_pct"

        # 3. If min/max and date is mentioned
        if operation in ("minimum", "maximum") and any(w in q for w in ("date", "earliest", "latest")):
            for col in ("award_date", "transaction_date", "approval_date", "date"):
                if col in schema:
                    return col

        # 4. Fallback: choose the primary numeric column
        if numeric_cols:
            return numeric_cols[0]

        if operation in ("sum", "average"):
            raise AnalysisPlanValidationError(
                f"Cannot perform '{operation}' because table has no numeric columns."
            )

        # For min/max, return first column
        return list(schema.keys())[0] if schema else None

    @classmethod
    def _detect_group_by(cls, q: str, schema: dict[str, str]) -> list[str]:
        """Detect grouping dimensions indicated by 'by <column>', 'per <column>', etc."""
        group_by: list[str] = []

        # Look for phrases like "by department", "per vendor", "each agency"
        group_patterns = [
            r"\bby\s+([a-zA-Z0-9_\s]+)",
            r"\bper\s+([a-zA-Z0-9_\s]+)",
            r"\beach\s+([a-zA-Z0-9_\s]+)",
            r"\bgrouped by\s+([a-zA-Z0-9_\s]+)",
        ]

        extracted_words: list[str] = []
        for pat in group_patterns:
            matches = re.findall(pat, q)
            for m in matches:
                # Stop at common prepositions/conjunctions
                clean_m = re.split(r"\b(in|for|with|where|order|sort|limit)\b", m)[0].strip()
                extracted_words.extend(clean_m.split())

        for col in schema:
            col_phrase = col.replace("_", " ")
            if col in extracted_words or col_phrase in q:
                if col not in group_by:
                    group_by.append(col)

        return group_by

    @classmethod
    def _detect_filters(cls, q: str, schema: dict[str, str]) -> list[FilterCondition]:
        """Detect filtering constraints from the inquiry."""
        filters: list[FilterCondition] = []

        # 1. Year filter (e.g. "in 2023", "for 2024", "fiscal year 2023")
        year_match = re.search(r"\b(20\d\d)\b", q)
        if year_match:
            year_val = int(year_match.group(1))
            if "fiscal_year" in schema:
                filters.append(FilterCondition(column="fiscal_year", operator="=", value=year_val))
            elif "year" in schema:
                filters.append(FilterCondition(column="year", operator="=", value=year_val))

        # 2. Boolean active flag filter
        if "active" in q and "is_active" in schema:
            if "inactive" in q or "not active" in q:
                filters.append(FilterCondition(column="is_active", operator="=", value=False))
            else:
                filters.append(FilterCondition(column="is_active", operator="=", value=True))

        # 3. Disbursed boolean flag
        if "disbursed" in schema:
            if "not disbursed" in q or "undisbursed" in q:
                filters.append(FilterCondition(column="disbursed", operator="=", value=False))
            elif "disbursed" in q:
                filters.append(FilterCondition(column="disbursed", operator="=", value=True))

        # 4. Department filter (e.g. "for Parks & Rec", "Transportation department")
        if "department" in schema:
            dept_map = {
                "parks & rec": "Parks & Rec",
                "parks": "Parks & Rec",
                "transportation": "Transportation",
                "public safety": "Public Safety",
                "sustainability": "Sustainability",
                "civic it": "Civic IT",
                "public works": "Public Works",
            }
            for key, dept_val in dept_map.items():
                if key in q:
                    # Only filter by department if department isn't the primary grouping
                    if f"by {key}" not in q and f"per {key}" not in q:
                        filters.append(FilterCondition(column="department", operator="=", value=dept_val))
                        break

        # 5. Numeric comparison (e.g. "greater than 50000", "> 100000")
        gt_match = re.search(r"(?:greater than|more than|above|>)\s*(\d+(?:\.\d+)?)", q)
        if gt_match:
            val = float(gt_match.group(1))
            numeric_cols = [c for c, t in schema.items() if t in ("INTEGER", "DOUBLE")]
            if numeric_cols:
                filters.append(FilterCondition(column=numeric_cols[0], operator=">", value=val))

        lt_match = re.search(r"(?:less than|fewer than|below|<)\s*(\d+(?:\.\d+)?)", q)
        if lt_match:
            val = float(lt_match.group(1))
            numeric_cols = [c for c, t in schema.items() if t in ("INTEGER", "DOUBLE")]
            if numeric_cols:
                filters.append(FilterCondition(column=numeric_cols[0], operator="<", value=val))

        return filters

    @classmethod
    def _detect_sorting(
        cls,
        q: str,
        operation: OperationType,
        target_column: str | None,
        group_by: list[str],
    ) -> list[SortCondition]:
        """Detect ordering directives."""
        sort_by: list[SortCondition] = []

        is_desc = any(w in q for w in ("highest", "top", "largest", "most", "descending", "desc"))
        is_asc = any(w in q for w in ("lowest", "least", "bottom", "smallest", "ascending", "asc"))

        if is_desc or is_asc:
            direction = "DESC" if is_desc else "ASC"
            # Target metric alias
            from app.analytics.planner import QueryPlanner
            mock_plan = AnalysisPlan(
                table_name="dummy",
                operation=operation,
                target_column=target_column,
                group_by=group_by,
            )
            metric_alias = QueryPlanner.get_metric_alias(mock_plan)
            sort_by.append(SortCondition(column=metric_alias, direction=direction))

        return sort_by

    @classmethod
    def _detect_limit(cls, q: str, default_limit: int) -> int:
        """Detect explicit limit like 'top 3', 'limit 5', 'first 10'."""
        top_match = re.search(r"\b(?:top|first|limit)\s+(\d+)\b", q)
        if top_match:
            val = int(top_match.group(1))
            return min(max(1, val), 1000)
        return min(max(1, default_limit), 1000)
