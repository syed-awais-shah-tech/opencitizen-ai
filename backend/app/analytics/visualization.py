"""Deterministic analytical result visualization and chart configuration engine.

IMPORTANT RULE:
Charts must be generated strictly from actual structured analytical results,
never invented or hallucinated by the LLM.

Supported safe chart types:
- bar: discrete categorical comparisons
- line: chronological / temporal trend sequences
- pie: compositional breakdowns (only when strictly appropriate: 2-7 positive slices)
- table: multidimensional, non-numeric, or high-cardinality result sets
"""

import re
from typing import Any, Optional

from app.analytics.schemas import (
    AnalysisPlan,
    ChartConfig,
    ChartSeries,
    ChartType,
    FormatType,
)

# Curated accessible dark-mode color palette
CHART_PALETTE = [
    "#06b6d4",  # Cyan
    "#10b981",  # Emerald
    "#8b5cf6",  # Purple
    "#f59e0b",  # Amber
    "#3b82f6",  # Blue
    "#f43f5e",  # Rose
    "#14b8a6",  # Teal
    "#ec4899",  # Pink
]

TEMPORAL_KEYWORDS = {
    "year",
    "yr",
    "date",
    "dt",
    "month",
    "quarter",
    "qtr",
    "fiscal_year",
    "fy",
    "period",
    "timestamp",
    "time",
    "day",
    "week",
}

CURRENCY_KEYWORDS = {
    "spend",
    "spending",
    "expense",
    "expenditure",
    "cost",
    "budget",
    "amount",
    "grant",
    "paid",
    "revenue",
    "dollar",
    "price",
    "award",
}

PERCENT_KEYWORDS = {"pct", "percent", "percentage", "rate", "ratio", "share"}
INTEGER_KEYWORDS = {"count", "row_count", "num_", "total_rows", "records", "quantity"}


class ChartGenerator:
    """Deterministic visualizer generating verified chart configurations from structured analytical results."""

    @classmethod
    def generate(
        cls,
        columns: list[str],
        rows: list[dict[str, Any]],
        table_name: str,
        plan: Optional[AnalysisPlan] = None,
        derivation: str = "",
    ) -> ChartConfig:
        """Analyze structured analytical output and automatically select the safest, most accurate visualization."""
        # 1. Check for Empty State
        if not rows or len(rows) == 0:
            return ChartConfig(
                chart_type="table",
                title=cls._build_title(plan, table_name),
                description=derivation or f"Analytical query executed on table '{table_name}'.",
                selection_reason="Result set contains 0 records; defaulting to empty table view.",
                is_empty=True,
                error_message="No analytical records match the specified query filters.",
                data=[],
                series=[],
            )

        # 2. Classify columns into dimensions (categorical/temporal) vs metrics (numeric)
        numeric_cols, non_numeric_cols = cls._classify_columns(columns, rows)

        # If plan specifies group_by, honor it as primary dimension candidates
        if plan and plan.group_by:
            dimension_cols = [col for col in plan.group_by if col in columns]
        else:
            dimension_cols = non_numeric_cols

        # Remaining numeric columns are candidate metrics
        metric_cols = [c for c in numeric_cols if c not in dimension_cols]

        # Edge case: No numeric metrics available at all (e.g., SELECT distinct department)
        if not metric_cols:
            return ChartConfig(
                chart_type="table",
                title=cls._build_title(plan, table_name),
                description=derivation or f"Tabular categorical records from '{table_name}'.",
                selection_reason="Result set has no numeric metrics for quantitative plotting; table view selected.",
                data=rows,
                series=[],
                is_empty=False,
            )

        # Edge case: Single scalar result (1 row, 1 column, e.g., SELECT count(*))
        if len(rows) == 1 and len(columns) == 1:
            series_list = cls._build_series(metric_cols, plan)
            return ChartConfig(
                chart_type="table",
                title=cls._build_title(plan, table_name),
                description=derivation or f"Scalar calculation on '{table_name}'.",
                selection_reason="Single scalar summary calculation; tabular display selected.",
                data=rows,
                series=series_list,
                is_empty=False,
            )

        # Determine primary dimension (X axis)
        x_key = dimension_cols[0] if dimension_cols else None
        if not x_key and non_numeric_cols:
            x_key = non_numeric_cols[0]
        elif not x_key and len(columns) > 1:
            # If all columns are numeric, pick first column as category if it looks like an identifier/year
            x_key = columns[0]
            metric_cols = [c for c in columns if c != x_key and c in numeric_cols]

        # If still no dimension key found, or multiple dimensional columns with complex hierarchy
        if not x_key or len(dimension_cols) > 2:
            return ChartConfig(
                chart_type="table",
                title=cls._build_title(plan, table_name),
                description=derivation or f"Multi-dimensional analytical records from '{table_name}'.",
                selection_reason="Multiple dimension hierarchy detected (>2 group dimensions); table view selected for clarity.",
                data=rows,
                series=cls._build_series(metric_cols, plan),
                is_empty=False,
            )

        # High cardinality threshold: > 30 rows cannot be legibly displayed on a standard bar/pie chart
        if len(rows) > 30:
            return ChartConfig(
                chart_type="table",
                title=cls._build_title(plan, table_name),
                description=derivation or f"High-cardinality records ({len(rows)} rows) from '{table_name}'.",
                selection_reason=f"High cardinality result set ({len(rows)} rows exceeds 30-item visual threshold); table view selected.",
                data=rows,
                series=cls._build_series(metric_cols, plan),
                is_empty=False,
            )

        # 3. Check for LINE chart suitability (temporal dimension)
        is_temporal = cls._is_temporal_column(x_key, rows)
        if is_temporal and len(rows) >= 2:
            series_list = cls._build_series(metric_cols, plan)
            return ChartConfig(
                chart_type="line",
                title=cls._build_title(plan, table_name),
                description=derivation or f"Temporal trend over '{x_key}'.",
                x_key=x_key,
                x_label=cls._format_label(x_key),
                y_label=cls._format_label(metric_cols[0]) if metric_cols else "Value",
                series=series_list,
                data=rows,
                selection_reason=f"Selected line chart because dimension '{x_key}' represents a chronological sequence across {len(rows)} periods.",
                is_empty=False,
            )

        # 4. Check for PIE chart suitability (only when strictly appropriate!)
        # Strict Pie Chart Criteria:
        # - Exactly 1 numeric metric
        # - Between 2 and 7 rows inclusive
        # - All metric values strictly > 0
        # - Operation is sum, count, or compositional (NOT average, min, or max)
        is_pie_candidate = (
            len(metric_cols) == 1
            and 2 <= len(rows) <= 7
            and cls._is_compositional_operation(plan)
            and cls._all_positive(rows, metric_cols[0])
        )

        if is_pie_candidate:
            metric_key = metric_cols[0]
            series_list = cls._build_series([metric_key], plan)
            return ChartConfig(
                chart_type="pie",
                title=cls._build_title(plan, table_name),
                description=derivation or f"Compositional distribution of '{metric_key}' across '{x_key}'.",
                x_key=x_key,
                x_label=cls._format_label(x_key),
                y_label=cls._format_label(metric_key),
                series=series_list,
                data=rows,
                selection_reason=f"Selected pie chart because result represents a compositional breakdown across {len(rows)} discrete categories with strictly positive values.",
                is_empty=False,
            )

        # 5. Default safe qualitative chart: BAR chart
        series_list = cls._build_series(metric_cols, plan)
        metric_names = ", ".join(cls._format_label(m) for m in metric_cols)
        return ChartConfig(
            chart_type="bar",
            title=cls._build_title(plan, table_name),
            description=derivation or f"Categorical comparison across '{x_key}'.",
            x_key=x_key,
            x_label=cls._format_label(x_key),
            y_label=cls._format_label(metric_cols[0]) if len(metric_cols) == 1 else "Value",
            series=series_list,
            data=rows,
            selection_reason=f"Selected bar chart for discrete categorical comparison of {metric_names} across '{x_key}' ({len(rows)} items).",
            is_empty=False,
        )

    # ---------------- Helper Functions ----------------

    @classmethod
    def _classify_columns(
        cls, columns: list[str], rows: list[dict[str, Any]]
    ) -> tuple[list[str], list[str]]:
        """Classify columns as numeric or non-numeric based on observed row data."""
        numeric_cols = []
        non_numeric_cols = []

        for col in columns:
            is_numeric = True
            observed = False
            for row in rows:
                val = row.get(col)
                if val is None:
                    continue
                observed = True
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    continue
                # If string, check if strictly numeric
                if isinstance(val, str):
                    try:
                        float(val)
                        continue
                    except ValueError:
                        pass
                is_numeric = False
                break

            if observed and is_numeric:
                numeric_cols.append(col)
            else:
                non_numeric_cols.append(col)

        return numeric_cols, non_numeric_cols

    @classmethod
    def _is_temporal_column(cls, col_name: str, rows: list[dict[str, Any]]) -> bool:
        """Check if a column represents a time/date dimension."""
        c_lower = col_name.lower()
        if any(kw in c_lower for kw in TEMPORAL_KEYWORDS):
            return True

        # Check values
        year_pattern = re.compile(r"^(19|20)\d{2}$")
        date_pattern = re.compile(r"^\d{4}[-/]\d{2}([-/]\d{2})?$")
        sample_vals = [str(r.get(col_name)) for r in rows if r.get(col_name) is not None]
        if sample_vals and (
            all(year_pattern.match(v.strip()) for v in sample_vals)
            or all(date_pattern.match(v.strip()) for v in sample_vals)
        ):
            return True

        return False

    @classmethod
    def _is_compositional_operation(cls, plan: Optional[AnalysisPlan]) -> bool:
        """Verify whether an operation represents a parts-of-a-whole aggregation (sum or count).

        Averages, minimums, and maximums do NOT sum to a total and must never be pie charts.
        """
        if not plan:
            return True
        return plan.operation in ("sum", "count")

    @classmethod
    def _all_positive(cls, rows: list[dict[str, Any]], metric_col: str) -> bool:
        """Check that all values in the metric column are strictly greater than zero."""
        for row in rows:
            val = row.get(metric_col)
            if val is None:
                return False
            try:
                if float(val) <= 0:
                    return False
            except (ValueError, TypeError):
                return False
        return True

    @classmethod
    def _build_series(
        cls, metric_cols: list[str], plan: Optional[AnalysisPlan]
    ) -> list[ChartSeries]:
        """Construct structured series metadata with appropriate formatting and colors."""
        series = []
        for idx, col in enumerate(metric_cols):
            color = CHART_PALETTE[idx % len(CHART_PALETTE)]
            fmt = cls._detect_format(col, plan)
            label = cls._format_label(col)
            series.append(
                ChartSeries(
                    key=col,
                    label=label,
                    color=color,
                    format_type=fmt,
                )
            )
        return series

    @classmethod
    def _detect_format(cls, col_name: str, plan: Optional[AnalysisPlan]) -> FormatType:
        """Infer numerical formatting representation from column names and plan."""
        c_lower = col_name.lower()
        if plan and plan.target_column:
            t_lower = plan.target_column.lower()
            if any(k in t_lower for k in CURRENCY_KEYWORDS):
                return "currency"

        if any(k in c_lower for k in CURRENCY_KEYWORDS):
            return "currency"
        if any(k in c_lower for k in PERCENT_KEYWORDS):
            return "percent"
        if any(k in c_lower for k in INTEGER_KEYWORDS) or (plan and plan.operation == "count"):
            return "integer"
        return "number"

    @classmethod
    def _format_label(cls, key: str) -> str:
        """Convert snake_case column names to clean, readable titles."""
        # Replace common prefixes
        clean = key.replace("_", " ").strip()
        words = clean.split()
        return " ".join(w.capitalize() for w in words)

    @classmethod
    def _build_title(cls, plan: Optional[AnalysisPlan], table_name: str) -> str:
        """Generate a concise, accurate title from the plan and table name."""
        clean_table = table_name.replace("_", " ").title()
        if plan:
            op_label = plan.operation.capitalize()
            if plan.target_column:
                target_label = cls._format_label(plan.target_column)
                if plan.group_by:
                    group_label = ", ".join(cls._format_label(g) for g in plan.group_by)
                    return f"{op_label} of {target_label} by {group_label}"
                return f"{op_label} of {target_label} ({clean_table})"
            if plan.group_by:
                group_label = ", ".join(cls._format_label(g) for g in plan.group_by)
                return f"Count by {group_label} ({clean_table})"
            return f"{op_label} Summary ({clean_table})"
        return f"Analysis: {clean_table}"
