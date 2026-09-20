"""Query planner compiling validated AnalysisPlan objects into strict, safe SQL."""

from typing import Any

from app.analytics.exceptions import (
    AnalysisPlanValidationError,
    ColumnNotFoundError,
    IncompatibleColumnTypeError,
    TableNotAllowedError,
)
from app.analytics.schemas import AnalysisPlan, FilterCondition, SortCondition
from app.analytics.validator import QueryValidator


class QueryPlanner:
    """Compiles and validates structured analysis plans against target table schemas."""

    OPERATION_SQL_MAP = {
        "count": "COUNT",
        "sum": "SUM",
        "average": "AVG",
        "minimum": "MIN",
        "maximum": "MAX",
    }

    OPERATION_ALIAS_PREFIX = {
        "count": "count",
        "sum": "sum",
        "average": "avg",
        "minimum": "min",
        "maximum": "max",
    }

    @classmethod
    def validate_plan(
        cls, plan: AnalysisPlan, table_schema: dict[str, str], allowed_tables: list[str]
    ) -> None:
        """Validate an AnalysisPlan against the concrete schema and allowed tables."""
        clean_table = plan.table_name.strip().lower()
        if clean_table not in [t.lower() for t in allowed_tables]:
            raise TableNotAllowedError(clean_table, allowed_tables)

        available_columns = list(table_schema.keys())

        # Validate target column for the operation
        if plan.operation in ("sum", "average", "minimum", "maximum"):
            if not plan.target_column:
                raise AnalysisPlanValidationError(
                    f"Operation '{plan.operation}' requires a 'target_column' to be specified."
                )
            target_clean = plan.target_column.strip().lower()
            if target_clean not in table_schema:
                raise ColumnNotFoundError(target_clean, clean_table, available_columns)

            col_type = table_schema[target_clean]
            if plan.operation in ("sum", "average") and col_type not in ("INTEGER", "DOUBLE"):
                raise IncompatibleColumnTypeError(plan.operation, target_clean, col_type)

        elif plan.operation == "count":
            if plan.target_column and plan.target_column.strip() not in ("*", ""):
                target_clean = plan.target_column.strip().lower()
                if target_clean not in table_schema:
                    raise ColumnNotFoundError(target_clean, clean_table, available_columns)

        # Validate grouping columns
        for group_col in plan.group_by:
            if group_col not in table_schema:
                raise ColumnNotFoundError(group_col, clean_table, available_columns)

        # Validate filters
        for f in plan.filters:
            if f.column not in table_schema:
                raise ColumnNotFoundError(f.column, clean_table, available_columns)

        # Validate sort columns
        metric_alias = cls.get_metric_alias(plan)
        valid_sort_targets = available_columns + plan.group_by + [metric_alias]
        for s in plan.sort_by:
            if s.column not in valid_sort_targets:
                raise ColumnNotFoundError(s.column, clean_table, valid_sort_targets)

    @classmethod
    def get_metric_alias(cls, plan: AnalysisPlan) -> str:
        """Derive standard output column alias for the primary aggregated metric."""
        prefix = cls.OPERATION_ALIAS_PREFIX.get(plan.operation, "val")
        if plan.operation == "count":
            if plan.target_column and plan.target_column.strip() not in ("*", ""):
                return f"count_{plan.target_column.strip().lower()}"
            return "count_total"
        target = (plan.target_column or "val").strip().lower()
        return f"{prefix}_{target}"

    @classmethod
    def compile_sql(
        cls, plan: AnalysisPlan, table_schema: dict[str, str], allowed_tables: list[str]
    ) -> tuple[str, list[Any], str]:
        """Compile a validated AnalysisPlan into safe DuckDB SQL and derivation text.

        Returns:
            sql: compiled and validated SQL query string
            params: list of bound parameter values
            derivation: human-readable explanation of computation
        """
        cls.validate_plan(plan, table_schema, allowed_tables)

        select_parts: list[str] = []
        params: list[Any] = []

        # 1. Group columns
        for g_col in plan.group_by:
            select_parts.append(g_col)

        # 2. Aggregation expression
        sql_func = cls.OPERATION_SQL_MAP[plan.operation]
        metric_alias = cls.get_metric_alias(plan)

        if plan.operation == "count":
            if plan.target_column and plan.target_column.strip() not in ("*", ""):
                target = plan.target_column.strip().lower()
                agg_expr = f"COUNT({target}) AS {metric_alias}"
            else:
                agg_expr = f"COUNT(*) AS {metric_alias}"
        elif plan.operation == "average":
            target = plan.target_column.strip().lower()  # type: ignore[union-attr]
            agg_expr = f"ROUND(AVG({target}), 2) AS {metric_alias}"
        elif plan.operation == "sum":
            target = plan.target_column.strip().lower()  # type: ignore[union-attr]
            agg_expr = f"ROUND(SUM({target}), 2) AS {metric_alias}"
        else:
            target = plan.target_column.strip().lower()  # type: ignore[union-attr]
            agg_expr = f"{sql_func}({target}) AS {metric_alias}"

        select_parts.append(agg_expr)

        # 3. FROM clause
        sql = f"SELECT {', '.join(select_parts)} FROM {plan.table_name}"

        # 4. WHERE clause (filtering)
        where_clauses: list[str] = []
        filter_descriptions: list[str] = []

        for f in plan.filters:
            col = f.column
            op = f.operator.upper()

            if op == "IS NULL":
                where_clauses.append(f"{col} IS NULL")
                filter_descriptions.append(f"{col} is null")
            elif op == "IS NOT NULL":
                where_clauses.append(f"{col} IS NOT NULL")
                filter_descriptions.append(f"{col} is not null")
            elif op == "IN":
                if not isinstance(f.value, (list, tuple, set)) or len(f.value) == 0:
                    raise AnalysisPlanValidationError(f"Filter 'IN' on '{col}' requires a non-empty list of values.")
                placeholders = ", ".join(["?"] * len(f.value))
                where_clauses.append(f"{col} IN ({placeholders})")
                params.extend(list(f.value))
                filter_descriptions.append(f"{col} in {f.value}")
            else:
                where_clauses.append(f"{col} {op} ?")
                params.append(f.value)
                filter_descriptions.append(f"{col} {op} {f.value}")

        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"

        # 5. GROUP BY clause (grouping)
        if plan.group_by:
            sql += f" GROUP BY {', '.join(plan.group_by)}"

        # 6. ORDER BY clause (sorting)
        if plan.sort_by:
            sort_clauses = [f"{s.column} {s.direction}" for s in plan.sort_by]
            sql += f" ORDER BY {', '.join(sort_clauses)}"
        elif plan.group_by:
            # Default sorting for grouped analytics: sort by metric descending
            sql += f" ORDER BY {metric_alias} DESC"

        # 7. LIMIT clause (safety limit)
        effective_limit = min(max(1, plan.limit), 1000)
        sql += f" LIMIT {effective_limit}"

        # 8. Run through QueryValidator as defense-in-depth
        validated_sql = QueryValidator.validate_sql(sql, allowed_tables)

        # 9. Format derivation
        op_name = plan.operation.upper()
        target_name = plan.target_column or "records"
        derivation = f"Computed {op_name} of {target_name} on table '{plan.table_name}'"
        if plan.group_by:
            derivation += f" grouped by {', '.join(plan.group_by)}"
        if filter_descriptions:
            derivation += f" filtered by [{' AND '.join(filter_descriptions)}]"
        if plan.sort_by:
            sort_desc = [f"{s.column} ({s.direction})" for s in plan.sort_by]
            derivation += f" sorted by {', '.join(sort_desc)}"
        derivation += f" with safety limit {effective_limit}."

        return validated_sql, params, derivation
