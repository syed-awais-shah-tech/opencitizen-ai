"""Controlled analytical query service coordinating the safe DuckDB analytical pipeline."""

from pathlib import Path
from sqlalchemy.orm import Session

from app.analytics.engine import DuckDBEngine, duckdb_engine
from app.analytics.exceptions import (
    AnalysisPlanValidationError,
    AnalyticsError,
    TableNotAllowedError,
)
from app.analytics.intent import IntentExtractor
from app.analytics.planner import QueryPlanner
from app.analytics.schemas import (
    AnalysisPlan,
    AnalyticalQueryRequest,
    AnalyticalResult,
    TableSchemaInfo,
)
from app.models.dataset import Dataset
from app.schemas.query import CalculationItem


class AnalyticsService:
    """Controlled analytical query service executing verified queries over structured civic datasets."""

    def __init__(self, engine: DuckDBEngine | None = None) -> None:
        self.engine = engine or duckdb_engine

    def resolve_target_table(
        self,
        db: Session | None,
        table_name: str | None = None,
        dataset_id: str | None = None,
        question: str | None = None,
    ) -> str:
        """Resolve and ensure the target table is registered in DuckDB."""
        # 1. Direct dataset_id lookup
        if dataset_id and db is not None:
            ds = db.get(Dataset, dataset_id)
            if ds:
                self._ensure_dataset_loaded_in_duckdb(ds)
                return ds.table_name

        # 2. Direct table_name specified
        if table_name:
            clean_name = table_name.strip().lower()
            if self.engine.has_table(clean_name):
                return clean_name
            # If not yet in DuckDB, check if it's in PostgreSQL
            if db is not None:
                ds = db.query(Dataset).filter(Dataset.table_name == clean_name).first()
                if ds:
                    self._ensure_dataset_loaded_in_duckdb(ds)
                    return ds.table_name
            raise TableNotAllowedError(clean_name, self.engine.get_registered_tables())

        # 3. Infer table from natural language question keywords
        if question:
            q_lower = question.lower()
            registered = self.engine.get_registered_tables()
            table_keywords = {
                "dept_expenses": ["expense", "spent", "spending", "department", "cost"],
                "vendor_contracts": ["vendor", "contract", "award", "contractor"],
                "civic_grants": ["grant", "recipient", "disbursed", "program"],
                "regional_unemployment": ["unemployment", "labor", "employment", "province", "jobless"],
                "capital_projects": ["project", "capital", "bikeway", "storm", "infrastructure"],
            }
            for tbl, keywords in table_keywords.items():
                if tbl in registered and any(kw in q_lower for kw in keywords):
                    return tbl

            # Fallback to first registered table if available
            if registered:
                return registered[0]

        raise AnalysisPlanValidationError(
            "Could not resolve a target table. Please specify 'table_name' or 'dataset_id'."
        )

    def _ensure_dataset_loaded_in_duckdb(self, dataset: Dataset) -> None:
        """Load a persisted dataset file from storage into DuckDB if not already loaded."""
        if self.engine.has_table(dataset.table_name):
            return

        storage_path = Path("storage/datasets") / dataset.id / f"data.{dataset.format.lower()}"
        if storage_path.exists():
            self.engine.register_file(
                table_name=dataset.table_name,
                file_path=storage_path,
                format_hint=dataset.format,
            )
        else:
            # Reconstruct table from preview or empty schema if storage file not found
            pass

    def run_analytical_query(
        self, request: AnalyticalQueryRequest, db: Session | None = None
    ) -> AnalyticalResult:
        """Execute the end-to-end controlled analytical pipeline:

        question
        → intent/analysis plan
        → validated SQL/query plan
        → DuckDB
        → structured result
        """
        # Step 1: Resolve target table
        target_table = self.resolve_target_table(
            db=db,
            table_name=request.table_name or (request.plan.table_name if request.plan else None),
            dataset_id=request.dataset_id,
            question=request.question,
        )

        # Step 2: Get table schema and allowed tables
        allowed_tables = self.engine.get_registered_tables()
        table_schema = self.engine.get_table_schema(target_table)

        # Step 3: Intent extraction → AnalysisPlan
        if request.plan:
            plan = request.plan
        elif request.question:
            plan = IntentExtractor.extract_plan(
                question=request.question,
                table_name=target_table,
                table_schema=table_schema,
                default_limit=request.limit,
            )
        else:
            raise AnalysisPlanValidationError(
                "Either a natural language 'question' or an explicit 'plan' must be provided."
            )

        # Step 4: Plan validation & SQL compilation
        validated_sql, params, derivation = QueryPlanner.compile_sql(
            plan=plan,
            table_schema=table_schema,
            allowed_tables=allowed_tables,
        )

        # Step 5: Execute in DuckDB
        columns, rows, execution_time_ms, rows_scanned = self.engine.execute_query(
            sql=validated_sql,
            params=params,
        )

        # Step 6: Formulate structured result
        return AnalyticalResult(
            plan=plan,
            query_sql=validated_sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            rows_scanned=rows_scanned,
            execution_time_ms=execution_time_ms,
            table_name=target_table,
            derivation=derivation,
        )

    def to_calculation_item(self, result: AnalyticalResult) -> CalculationItem:
        """Transform an AnalyticalResult into a CalculationItem for QA query responses."""
        return CalculationItem(
            query=result.query_sql,
            execution_time_ms=result.execution_time_ms,
            rows_scanned=result.rows_scanned,
            table_name=result.table_name,
            raw_rows=result.rows,
            derivation=result.derivation,
        )

    def list_tables(self) -> list[TableSchemaInfo]:
        """List all analytical tables currently available in DuckDB."""
        results = []
        for tbl in self.engine.get_registered_tables():
            try:
                info = self.engine.get_table_info(tbl)
                results.append(info)
            except Exception:
                pass
        return results


# Shared singleton service instance
analytics_service = AnalyticsService()
