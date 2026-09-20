"""Comprehensive test suite for DuckDB analytical query service, validation, and operations."""

import pytest
from fastapi.testclient import TestClient

from app.analytics.engine import DuckDBEngine, duckdb_engine
from app.analytics.exceptions import (
    AnalysisPlanValidationError,
    ColumnNotFoundError,
    IncompatibleColumnTypeError,
    SQLValidationError,
    TableNotAllowedError,
)
from app.analytics.intent import IntentExtractor
from app.analytics.planner import QueryPlanner
from app.analytics.schemas import (
    AnalysisPlan,
    AnalyticalQueryRequest,
    FilterCondition,
    SortCondition,
)
from app.analytics.validator import QueryValidator
from app.main import app
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def duckdb_fixture_engine():
    """Create an isolated DuckDB in-memory engine with seeded civic tables."""
    engine = DuckDBEngine(database=":memory:")
    engine.seed_civic_tables()
    return engine


@pytest.fixture
def test_service(duckdb_fixture_engine):
    """Create an analytics service backed by the test engine."""
    return AnalyticsService(engine=duckdb_fixture_engine)


# ==============================================================================
# 1. Analytical Operations Tests (count, sum, avg, min, max, group, sort, filter)
# ==============================================================================

def test_operation_count_total(test_service):
    """Test COUNT(*) operation without grouping."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="count",
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    assert "count_total" in res.columns
    assert res.rows[0]["count_total"] == 7
    assert "COUNT(*)" in res.query_sql


def test_operation_count_by_group(test_service):
    """Test COUNT(*) grouped by a categorical dimension."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="count",
        group_by=["department"],
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count > 1
    assert "department" in res.columns
    assert "count_total" in res.columns
    depts = [r["department"] for r in res.rows]
    assert "Parks & Rec" in depts
    assert "Transportation" in depts


def test_operation_sum_numeric(test_service):
    """Test SUM operation on a numeric metric."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="sum",
        target_column="amount",
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    assert "sum_amount" in res.columns
    # 45000 + 12400 + 89000 + 32000 + 18500 + 125000 + 41000 = 362900.0
    assert res.rows[0]["sum_amount"] == 362900.0
    assert "ROUND(SUM(amount), 2)" in res.query_sql


def test_operation_average_numeric(test_service):
    """Test AVG/average operation on a numeric metric."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="average",
        target_column="amount",
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    assert "avg_amount" in res.columns
    # 362900.0 / 7 = 51842.86
    assert abs(res.rows[0]["avg_amount"] - 51842.86) < 0.05


def test_operation_minimum(test_service):
    """Test MIN operation on a numeric column."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="minimum",
        target_column="amount",
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    assert res.rows[0]["min_amount"] == 12400.0


def test_operation_maximum(test_service):
    """Test MAX operation on a numeric column."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="maximum",
        target_column="amount",
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    assert res.rows[0]["max_amount"] == 125000.0


def test_operation_grouping_and_sorting(test_service):
    """Test grouping by department and sorting by aggregate sum descending."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="sum",
        target_column="amount",
        group_by=["department"],
        sort_by=[SortCondition(column="sum_amount", direction="DESC")],
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count >= 2
    # First row should have the highest total spent
    first_row = res.rows[0]
    second_row = res.rows[1]
    assert first_row["sum_amount"] >= second_row["sum_amount"]
    assert first_row["department"] == "Transportation"  # 89000 + 125000 = 214000


def test_operation_filtering_equality_and_comparison(test_service):
    """Test filtering by fiscal year equality and amount threshold."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="sum",
        target_column="amount",
        filters=[
            FilterCondition(column="fiscal_year", operator="=", value=2023),
            FilterCondition(column="amount", operator=">", value=40000),
        ],
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    # 2023 rows > 40000: 45000 (Parks) + 89000 (Transport) + 125000 (Transport) = 259000.0
    assert res.rows[0]["sum_amount"] == 259000.0


def test_operation_filtering_in_and_is_not_null(test_service):
    """Test IN list membership and IS NOT NULL filter operations."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="count",
        filters=[
            FilterCondition(column="department", operator="IN", value=["Transportation", "Public Safety"]),
            FilterCondition(column="vendor_name", operator="IS NOT NULL"),
        ],
    )
    res = test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))
    assert res.row_count == 1
    # Transportation has 2, Public Safety has 2 = 4 total
    assert res.rows[0]["count_total"] == 4


# ==============================================================================
# 2. Pipeline: question → intent/analysis plan → validated SQL → DuckDB
# ==============================================================================

def test_pipeline_natural_language_sum_grouping(test_service):
    """Test full pipeline from natural language question to DuckDB structured execution."""
    question = "What is the total expenditure by department in 2023?"
    req = AnalyticalQueryRequest(question=question, table_name="dept_expenses")
    res = test_service.run_analytical_query(req)

    assert res.plan.operation == "sum"
    assert res.plan.target_column == "amount"
    assert "department" in res.plan.group_by
    assert any(f.column == "fiscal_year" and f.value == 2023 for f in res.plan.filters)
    assert res.row_count > 0
    assert "SELECT" in res.query_sql
    assert "ROUND(SUM(amount), 2)" in res.query_sql
    assert res.derivation != ""
    assert res.execution_time_ms >= 0.0


def test_pipeline_natural_language_count_contracts(test_service):
    """Test natural language question for contract counting."""
    question = "How many active vendor contracts are there?"
    req = AnalyticalQueryRequest(question=question, table_name="vendor_contracts")
    res = test_service.run_analytical_query(req)

    assert res.plan.operation == "count"
    assert any(f.column == "is_active" and f.value is True for f in res.plan.filters)
    assert res.rows[0]["count_total"] == 3


def test_pipeline_natural_language_average_with_limit(test_service):
    """Test average query with top N limit in question."""
    question = "Top 3 departments by average spent"
    req = AnalyticalQueryRequest(question=question, table_name="dept_expenses")
    res = test_service.run_analytical_query(req)

    assert res.plan.operation == "average"
    assert res.plan.limit == 3
    assert len(res.rows) <= 3


# ==============================================================================
# 3. Query Validation and Security Limits Tests (Invalid Requests)
# ==============================================================================

def test_validation_rejects_ddl_and_dml():
    """Verify that DROP, DELETE, UPDATE, INSERT statements are strictly rejected."""
    allowed = ["dept_expenses"]

    with pytest.raises(SQLValidationError, match="Only read-only SELECT queries"):
        QueryValidator.validate_sql("DROP TABLE dept_expenses", allowed)

    with pytest.raises(SQLValidationError, match="Only read-only SELECT queries"):
        QueryValidator.validate_sql("DELETE FROM dept_expenses WHERE amount > 0", allowed)

    with pytest.raises(SQLValidationError, match="Multiple stacked SQL statements"):
        QueryValidator.validate_sql("SELECT * FROM dept_expenses; DROP TABLE dept_expenses", allowed)

    with pytest.raises(SQLValidationError, match="Forbidden SQL keyword"):
        QueryValidator.validate_sql("SELECT DROP FROM dept_expenses", allowed)

    with pytest.raises(SQLValidationError, match="Multiple stacked SQL statements"):
        QueryValidator.validate_sql("SELECT * FROM dept_expenses; SELECT 1", allowed)


def test_validation_rejects_filesystem_and_external_functions():
    """Verify that calls to read_csv, read_parquet, and duckdb settings are rejected in raw queries."""
    allowed = ["dept_expenses"]
    with pytest.raises(SQLValidationError, match="Direct filesystem/external function"):
        QueryValidator.validate_sql("SELECT * FROM read_csv('/etc/passwd')", allowed)

    with pytest.raises(SQLValidationError, match="Direct filesystem/external function"):
        QueryValidator.validate_sql("SELECT * FROM read_parquet('secret.parquet')", allowed)


def test_validation_rejects_sql_comments():
    """Verify SQL comments used in injection techniques are rejected."""
    allowed = ["dept_expenses"]
    with pytest.raises(SQLValidationError, match="SQL comments are not permitted"):
        QueryValidator.validate_sql("SELECT * FROM dept_expenses -- bypass filter", allowed)

    with pytest.raises(SQLValidationError, match="SQL comments are not permitted"):
        QueryValidator.validate_sql("SELECT * FROM dept_expenses /* inline block */", allowed)


def test_validation_rejects_unregistered_table(test_service):
    """Verify queries referencing unregistered tables are rejected."""
    plan = AnalysisPlan(
        table_name="unregistered_secret_table",
        operation="count",
    )
    with pytest.raises(TableNotAllowedError, match="not registered or not permitted"):
        test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))


def test_validation_rejects_nonexistent_column(test_service):
    """Verify queries referencing non-existent columns are rejected."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="sum",
        target_column="nonexistent_column",
    )
    with pytest.raises(ColumnNotFoundError, match="does not exist in table 'dept_expenses'"):
        test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))


def test_validation_rejects_incompatible_column_type(test_service):
    """Verify SUM or AVERAGE on non-numeric column (VARCHAR) is rejected."""
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="sum",
        target_column="vendor_name",  # VARCHAR column
    )
    with pytest.raises(IncompatibleColumnTypeError, match="cannot be performed on column 'vendor_name' of type 'VARCHAR'"):
        test_service.run_analytical_query(AnalyticalQueryRequest(plan=plan))


def test_validation_clamps_limit_bounds():
    """Verify that limit values are clamped to safe maximum bounds."""
    allowed = ["dept_expenses"]
    sql_high = QueryValidator.validate_sql("SELECT * FROM dept_expenses LIMIT 5000", allowed)
    assert "LIMIT 1000" in sql_high

    sql_none = QueryValidator.validate_sql("SELECT * FROM dept_expenses", allowed)
    assert "LIMIT 100" in sql_none


# ==============================================================================
# 4. API Endpoints Tests (/api/v1/analytics/...)
# ==============================================================================

def test_api_analytics_query_natural_language(client):
    """Test POST /api/v1/analytics/query with a natural language inquiry."""
    payload = {
        "question": "What is the total expenditure by department in 2023?",
        "table_name": "dept_expenses",
        "limit": 10,
    }
    response = client.post("/api/v1/analytics/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "dept_expenses"
    assert data["row_count"] > 0
    assert "sum_amount" in data["columns"]
    assert "ROUND(SUM(amount), 2)" in data["query_sql"]
    assert data["execution_time_ms"] >= 0.0


def test_api_analytics_query_explicit_plan(client):
    """Test POST /api/v1/analytics/query with a pre-validated AnalysisPlan."""
    payload = {
        "plan": {
            "table_name": "vendor_contracts",
            "operation": "maximum",
            "target_column": "contract_value",
            "group_by": ["department"],
            "limit": 5,
        }
    }
    response = client.post("/api/v1/analytics/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "vendor_contracts"
    assert "max_contract_value" in data["columns"]
    assert len(data["rows"]) <= 5


def test_api_analytics_query_invalid_table(client):
    """Test POST /api/v1/analytics/query with invalid table returns 403 Forbidden."""
    payload = {
        "table_name": "nonexistent_table_99",
        "question": "Total spent",
    }
    response = client.post("/api/v1/analytics/query", json=payload)
    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == "TABLE_NOT_ALLOWED"


def test_api_analytics_query_invalid_column(client):
    """Test POST /api/v1/analytics/query with invalid column returns 422 Unprocessable Content."""
    payload = {
        "plan": {
            "table_name": "dept_expenses",
            "operation": "sum",
            "target_column": "invalid_column_name",
        }
    }
    response = client.post("/api/v1/analytics/query", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "COLUMN_NOT_FOUND"


def test_api_analytics_query_incompatible_type(client):
    """Test POST /api/v1/analytics/query with incompatible column type returns 422."""
    payload = {
        "plan": {
            "table_name": "dept_expenses",
            "operation": "average",
            "target_column": "vendor_name",
        }
    }
    response = client.post("/api/v1/analytics/query", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INCOMPATIBLE_COLUMN_TYPE"


def test_api_list_tables(client):
    """Test GET /api/v1/analytics/tables."""
    response = client.get("/api/v1/analytics/tables")
    assert response.status_code == 200
    tables = response.json()
    assert isinstance(tables, list)
    table_names = [t["table_name"] for t in tables]
    assert "dept_expenses" in table_names
    assert "vendor_contracts" in table_names


def test_api_get_table_info_success(client):
    """Test GET /api/v1/analytics/tables/{table_name} for registered table."""
    response = client.get("/api/v1/analytics/tables/dept_expenses")
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "dept_expenses"
    col_names = [c["name"] for c in data["columns"]]
    assert "department" in col_names
    assert "amount" in col_names
    assert data["row_count"] >= 7


def test_api_get_table_info_not_found(client):
    """Test GET /api/v1/analytics/tables/{table_name} for unknown table returns 403."""
    response = client.get("/api/v1/analytics/tables/unknown_tbl")
    assert response.status_code == 403
