"""DuckDB Analytical Engine wrapper for high-performance in-process SQL execution."""

import datetime
import decimal
import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from app.analytics.exceptions import AnalyticsError, TableNotAllowedError
from app.analytics.schemas import TableColumnInfo, TableSchemaInfo


class DuckDBEngine:
    """In-process DuckDB analytical engine managing datasets, views, and read-only query execution."""

    def __init__(self, database: str = ":memory:") -> None:
        self.database = database
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._table_registry: dict[str, dict[str, str]] = {}
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Create and configure the DuckDB connection with safety boundaries."""
        self._conn = duckdb.connect(self.database)
        # Apply strict query execution limits
        self._conn.execute("SET threads = 2;")
        self._conn.execute("SET memory_limit = '512MB';")

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._initialize_connection()
        assert self._conn is not None
        return self._conn

    def register_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Register a Pandas DataFrame as an in-memory table/view in DuckDB."""
        clean_name = table_name.strip().lower()
        self.conn.execute(f"CREATE OR REPLACE TABLE {clean_name} AS SELECT * FROM df;")
        self._cache_table_schema(clean_name)

    def register_file(self, table_name: str, file_path: Path | str, format_hint: str = "CSV") -> None:
        """Register a structured dataset file (CSV, Parquet, or JSON) into DuckDB."""
        path = Path(file_path).resolve()
        clean_name = table_name.strip().lower()

        if not path.exists():
            raise AnalyticsError(f"Dataset file does not exist at '{path}'.")

        ext = path.suffix.lower()
        path_str = str(path).replace("\\", "/")

        if ext in (".parquet", ".pq") or format_hint.upper() == "PARQUET":
            query = f"CREATE OR REPLACE VIEW {clean_name} AS SELECT * FROM read_parquet('{path_str}');"
        elif ext == ".json" or format_hint.upper() == "JSON":
            query = f"CREATE OR REPLACE VIEW {clean_name} AS SELECT * FROM read_json_auto('{path_str}');"
        else:
            query = f"CREATE OR REPLACE VIEW {clean_name} AS SELECT * FROM read_csv_auto('{path_str}', header=True);"

        self.conn.execute(query)
        self._cache_table_schema(clean_name)

    def _cache_table_schema(self, table_name: str) -> None:
        """Introspect and normalize column data types for a registered table."""
        clean_name = table_name.strip().lower()
        try:
            desc = self.conn.execute(f"DESCRIBE {clean_name};").fetchall()
            schema: dict[str, str] = {}
            for row in desc:
                col_name = str(row[0]).lower()
                raw_type = str(row[1]).upper()
                norm_type = self._normalize_duckdb_type(raw_type)
                schema[col_name] = norm_type
            self._table_registry[clean_name] = schema
        except Exception as e:
            raise AnalyticsError(f"Failed to inspect schema for table '{table_name}': {e}") from e

    @staticmethod
    def _normalize_duckdb_type(duckdb_type: str) -> str:
        """Map DuckDB SQL types to standard schema types: VARCHAR, DOUBLE, INTEGER, DATE, BOOLEAN."""
        t = duckdb_type.upper()
        if any(i in t for i in ("INT", "BIGINT", "SMALLINT", "TINYINT", "HUGEINT")):
            return "INTEGER"
        if any(f in t for f in ("FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL")):
            return "DOUBLE"
        if any(d in t for d in ("DATE", "TIMESTAMP", "TIME")):
            return "DATE"
        if "BOOL" in t:
            return "BOOLEAN"
        return "VARCHAR"

    def get_registered_tables(self) -> list[str]:
        """Return the list of currently registered table identifiers."""
        return list(self._table_registry.keys())

    def has_table(self, table_name: str) -> bool:
        """Check if a table identifier is registered in DuckDB."""
        return table_name.strip().lower() in self._table_registry

    def get_table_schema(self, table_name: str) -> dict[str, str]:
        """Return column name to normalized type mapping for a registered table."""
        clean_name = table_name.strip().lower()
        if clean_name not in self._table_registry:
            raise TableNotAllowedError(clean_name, list(self._table_registry.keys()))
        return self._table_registry[clean_name]

    def get_table_row_count(self, table_name: str) -> int:
        """Get the current row count of a table."""
        clean_name = table_name.strip().lower()
        if not self.has_table(clean_name):
            return 0
        res = self.conn.execute(f"SELECT COUNT(*) FROM {clean_name};").fetchone()
        return int(res[0]) if res else 0

    def get_table_info(self, table_name: str) -> TableSchemaInfo:
        """Retrieve full schema metadata for an analytical table."""
        schema = self.get_table_schema(table_name)
        cols = [TableColumnInfo(name=name, type=dtype) for name, dtype in schema.items()]
        row_count = self.get_table_row_count(table_name)
        return TableSchemaInfo(table_name=table_name, columns=cols, row_count=row_count)

    def execute_query(
        self, sql: str, params: list[Any] | None = None
    ) -> tuple[list[str], list[dict[str, Any]], float, int]:
        """Execute a validated SQL query against DuckDB and return structured results.

        Returns:
            columns: list of output column names
            rows: list of dictionary records
            execution_time_ms: latency in milliseconds
            rows_scanned: estimated number of rows scanned
        """
        from app.analytics.validator import QueryValidator

        # Defense-in-depth: validate incoming SQL against safety boundaries and registered tables
        validated_sql = QueryValidator.validate_sql(sql, self.get_registered_tables())

        start = time.perf_counter()
        cursor = self.conn.cursor()

        try:
            if params:
                cursor.execute(validated_sql, params)
            else:
                cursor.execute(validated_sql)

            # Extract output column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch rows and serialize types
            raw_data = cursor.fetchall()
            serialized_rows: list[dict[str, Any]] = []

            for row in raw_data:
                record: dict[str, Any] = {}
                for col_name, val in zip(columns, row):
                    record[col_name] = self._serialize_value(val)
                serialized_rows.append(record)

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            rows_scanned = len(serialized_rows)

            return columns, serialized_rows, elapsed_ms, rows_scanned

        except Exception as e:
            raise AnalyticsError(f"DuckDB execution error: {e}") from e
        finally:
            cursor.close()

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        """Convert DuckDB types to standard JSON-compatible Python primitives."""
        if val is None:
            return None
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val.isoformat()
        if isinstance(val, decimal.Decimal):
            return float(val)
        if isinstance(val, (int, float, bool, str)):
            return val
        return str(val)

    def seed_civic_tables(self) -> None:
        """Pre-populate sample civic municipal tables for interactive analytics and testing."""
        # 1. dept_expenses
        dept_expenses_df = pd.DataFrame([
            {"department": "Parks & Rec", "fiscal_year": 2023, "amount": 45000.0, "vendor_name": "Apex Facility Services", "fund_source": "General", "transaction_date": "2023-04-12"},
            {"department": "Parks & Rec", "fiscal_year": 2023, "amount": 12400.0, "vendor_name": "Civic Turf & Landscape", "fund_source": "Special", "transaction_date": "2023-05-18"},
            {"department": "Transportation", "fiscal_year": 2023, "amount": 89000.0, "vendor_name": "Metro Asphalt Corp", "fund_source": "Capital", "transaction_date": "2023-06-01"},
            {"department": "Public Safety", "fiscal_year": 2023, "amount": 32000.0, "vendor_name": "Sentinel Telemetry", "fund_source": "General", "transaction_date": "2023-07-22"},
            {"department": "Civic IT", "fiscal_year": 2023, "amount": 18500.0, "vendor_name": "CloudLink Systems", "fund_source": "General", "transaction_date": "2023-08-14"},
            {"department": "Transportation", "fiscal_year": 2023, "amount": 125000.0, "vendor_name": "Apex Facility Services", "fund_source": "Capital", "transaction_date": "2023-09-01"},
            {"department": "Public Safety", "fiscal_year": 2024, "amount": 41000.0, "vendor_name": "Sentinel Telemetry", "fund_source": "General", "transaction_date": "2024-01-10"},
        ])
        self.register_dataframe("dept_expenses", dept_expenses_df)

        # 2. vendor_contracts
        contracts_df = pd.DataFrame([
            {"contract_id": "CTR-2023-091", "vendor_name": "Apex Facility Services", "department": "Parks & Rec", "contract_value": 1250000.0, "award_date": "2023-01-15", "end_date": "2025-01-15", "is_active": True},
            {"contract_id": "CTR-2023-142", "vendor_name": "Metro Asphalt Corp", "department": "Transportation", "contract_value": 4800000.0, "award_date": "2023-03-01", "end_date": "2026-03-01", "is_active": True},
            {"contract_id": "CTR-2023-205", "vendor_name": "CleanGrid Solutions", "department": "Sustainability", "contract_value": 2100000.0, "award_date": "2023-05-10", "end_date": "2025-12-31", "is_active": True},
            {"contract_id": "CTR-2023-301", "vendor_name": "Sentinel Telemetry", "department": "Public Safety", "contract_value": 850000.0, "award_date": "2023-08-15", "end_date": "2024-08-15", "is_active": False},
        ])
        self.register_dataframe("vendor_contracts", contracts_df)

        # 3. civic_grants
        grants_df = pd.DataFrame([
            {"grant_id": "GRN-2024-001", "recipient": "Westside Youth Arts", "grant_amount": 45000.0, "disbursed": True, "approval_date": "2024-01-15", "program_name": "Community Cultural Fund"},
            {"grant_id": "GRN-2024-002", "recipient": "Harbor Clean Waters", "grant_amount": 120000.0, "disbursed": True, "approval_date": "2024-02-20", "program_name": "Environmental Resilience"},
            {"grant_id": "GRN-2024-003", "recipient": "Downtown Urban Greenery", "grant_amount": 35000.0, "disbursed": False, "approval_date": "2024-03-05", "program_name": "Urban Canopy"},
            {"grant_id": "GRN-2024-004", "recipient": "Elder Transit Link", "grant_amount": 78000.0, "disbursed": True, "approval_date": "2024-04-12", "program_name": "Civic Mobility Grant"},
        ])
        self.register_dataframe("civic_grants", grants_df)

        # 4. regional_unemployment
        unemployment_df = pd.DataFrame([
            {"province": "Province A", "unemployment_rate": 6.2, "labor_force": 1200000, "year": 2023},
            {"province": "Province B", "unemployment_rate": 5.4, "labor_force": 2500000, "year": 2023},
            {"province": "Province X", "unemployment_rate": 9.8, "labor_force": 850000, "year": 2023},
            {"province": "Province Y", "unemployment_rate": 7.1, "labor_force": 1800000, "year": 2023},
        ])
        self.register_dataframe("regional_unemployment", unemployment_df)

        # 5. public_development_projects (Stage 18 Geospatial Civic Projects)
        development_projects_df = pd.DataFrame([
            {
                "project_id": "DEV-101",
                "project_name": "East Riverside Transit Hub & Affordable Housing",
                "category": "Transportation",
                "status": "In Progress",
                "budget": 4200000.0,
                "spent_to_date": 2730000.0,
                "completion_pct": 65.0,
                "lead_agency": "Transportation & Public Works",
                "latitude": 30.2450,
                "longitude": -97.7280,
                "target_completion": "2025-11-30",
            },
            {
                "project_id": "DEV-102",
                "project_name": "Barton Creek Greenbelt Ecological Restoration",
                "category": "Parks & Environment",
                "status": "Completed",
                "budget": 1850000.0,
                "spent_to_date": 1850000.0,
                "completion_pct": 100.0,
                "lead_agency": "Parks & Rec",
                "latitude": 30.2580,
                "longitude": -97.7840,
                "target_completion": "2024-06-15",
            },
            {
                "project_id": "DEV-103",
                "project_name": "Zilker Park Community Solar & Rec Facility",
                "category": "Parks & Environment",
                "status": "In Progress",
                "budget": 950000.0,
                "spent_to_date": 285000.0,
                "completion_pct": 30.0,
                "lead_agency": "Sustainability Office",
                "latitude": 30.2670,
                "longitude": -97.7710,
                "target_completion": "2025-08-20",
            },
            {
                "project_id": "DEV-104",
                "project_name": "Airport Boulevard Corridor Modernization",
                "category": "Transportation",
                "status": "Planned",
                "budget": 6800000.0,
                "spent_to_date": 0.0,
                "completion_pct": 0.0,
                "lead_agency": "Transportation Dept",
                "latitude": 30.3120,
                "longitude": -97.7150,
                "target_completion": "2026-12-31",
            },
            {
                "project_id": "DEV-105",
                "project_name": "Pleasant Valley Civic Health Clinic",
                "category": "Healthcare",
                "status": "In Progress",
                "budget": 3100000.0,
                "spent_to_date": 1550000.0,
                "completion_pct": 50.0,
                "lead_agency": "Public Health",
                "latitude": 30.2310,
                "longitude": -97.7120,
                "target_completion": "2025-09-15",
            },
            {
                "project_id": "DEV-106",
                "project_name": "Mueller Branch Library & Community Center",
                "category": "Public Facilities",
                "status": "Completed",
                "budget": 2400000.0,
                "spent_to_date": 2400000.0,
                "completion_pct": 100.0,
                "lead_agency": "Library Dept",
                "latitude": 30.3010,
                "longitude": -97.7050,
                "target_completion": "2024-04-30",
            },
            {
                "project_id": "DEV-107",
                "project_name": "North Lamar Stormwater & Bioswale Project",
                "category": "Infrastructure",
                "status": "In Progress",
                "budget": 1600000.0,
                "spent_to_date": 1280000.0,
                "completion_pct": 80.0,
                "lead_agency": "Watershed Protection",
                "latitude": 30.3450,
                "longitude": -97.7210,
                "target_completion": "2025-05-30",
            },
            {
                "project_id": "DEV-108",
                "project_name": "South Congress Pedestrian Safety Corridor",
                "category": "Transportation",
                "status": "Planned",
                "budget": 890000.0,
                "spent_to_date": 120000.0,
                "completion_pct": 15.0,
                "lead_agency": "Transportation Dept",
                "latitude": 30.2480,
                "longitude": -97.7530,
                "target_completion": "2026-03-31",
            },
        ])
        self.register_dataframe("public_development_projects", development_projects_df)


# Shared singleton engine instance
duckdb_engine = DuckDBEngine()
duckdb_engine.seed_civic_tables()
