"""Unit and integration tests for analytical result visualization and chart configuration generation."""

import pytest
from fastapi.testclient import TestClient

from app.analytics.schemas import AnalysisPlan, AnalyticalQueryRequest, AnalyticalResult
from app.analytics.visualization import ChartGenerator
from app.main import app
from app.orchestration.orchestrator import QueryOrchestrator
from app.schemas.query import QueryRequest
from app.services.analytics_service import analytics_service


@pytest.fixture
def client():
    return TestClient(app)


def test_empty_result_state():
    """Empty result sets must produce an explicit empty table state with explanatory messaging."""
    config = ChartGenerator.generate(
        columns=["department", "total_expense"],
        rows=[],
        table_name="dept_expenses",
        derivation="Sum of expenditure by department",
    )
    assert config.chart_type == "table"
    assert config.is_empty is True
    assert config.error_message is not None
    assert "No analytical records" in config.error_message
    assert len(config.data) == 0
    assert len(config.series) == 0


def test_bar_chart_generation():
    """Discrete categorical dimensions with numeric metrics should select a bar chart."""
    rows = [
        {"department": "Police", "total_spending": 4500000.0},
        {"department": "Fire", "total_spending": 3200000.0},
        {"department": "Parks & Rec", "total_spending": 1800000.0},
        {"department": "Public Works", "total_spending": 2900000.0},
        {"department": "Library", "total_spending": 950000.0},
        {"department": "Health", "total_spending": 1400000.0},
        {"department": "Transportation", "total_spending": 3800000.0},
        {"department": "Administration", "total_spending": 1100000.0},
        {"department": "Information Tech", "total_spending": 2100000.0},
    ]
    plan = AnalysisPlan(
        table_name="dept_expenses",
        operation="sum",
        target_column="amount",
        group_by=["department"],
    )
    config = ChartGenerator.generate(
        columns=["department", "total_spending"],
        rows=rows,
        table_name="dept_expenses",
        plan=plan,
        derivation="Sum of amount grouped by department",
    )

    assert config.chart_type == "bar"
    assert config.x_key == "department"
    assert config.is_empty is False
    assert len(config.series) == 1
    assert config.series[0].key == "total_spending"
    assert config.series[0].format_type == "currency"
    assert "bar chart" in config.selection_reason.lower()


def test_line_chart_generation_temporal_year():
    """Temporal sequence (e.g. years) with numeric metric should select a line chart."""
    rows = [
        {"year": 2020, "total_budget": 12000000.0},
        {"year": 2021, "total_budget": 13500000.0},
        {"year": 2022, "total_budget": 14200000.0},
        {"year": 2023, "total_budget": 15800000.0},
        {"year": 2024, "total_budget": 16900000.0},
    ]
    plan = AnalysisPlan(
        table_name="capital_projects",
        operation="sum",
        target_column="budget",
        group_by=["year"],
    )
    config = ChartGenerator.generate(
        columns=["year", "total_budget"],
        rows=rows,
        table_name="capital_projects",
        plan=plan,
    )

    assert config.chart_type == "line"
    assert config.x_key == "year"
    assert config.is_empty is False
    assert len(config.series) == 1
    assert config.series[0].key == "total_budget"
    assert config.series[0].format_type == "currency"
    assert "line chart" in config.selection_reason.lower()


def test_line_chart_generation_date_format():
    """Dates formatted as YYYY-MM-DD should select a line chart."""
    rows = [
        {"report_date": "2023-01-01", "cases": 120},
        {"report_date": "2023-02-01", "cases": 145},
        {"report_date": "2023-03-01", "cases": 190},
    ]
    config = ChartGenerator.generate(
        columns=["report_date", "cases"],
        rows=rows,
        table_name="health_stats",
    )
    assert config.chart_type == "line"
    assert config.x_key == "report_date"


def test_pie_chart_appropriate():
    """Pie chart must be selected only when: 1 metric, 2-7 rows, all positive, compositional operation."""
    rows = [
        {"category": "Affordable Housing", "allocation": 450000.0},
        {"category": "Park Infrastructure", "allocation": 320000.0},
        {"category": "Youth Programs", "allocation": 180000.0},
        {"category": "Transit Improvements", "allocation": 250000.0},
    ]
    plan = AnalysisPlan(
        table_name="civic_grants",
        operation="sum",
        target_column="amount",
        group_by=["category"],
    )
    config = ChartGenerator.generate(
        columns=["category", "allocation"],
        rows=rows,
        table_name="civic_grants",
        plan=plan,
    )

    assert config.chart_type == "pie"
    assert config.x_key == "category"
    assert len(config.series) == 1
    assert config.series[0].key == "allocation"
    assert "pie chart" in config.selection_reason.lower()


def test_pie_chart_rejected_when_too_many_slices():
    """Pie chart must be rejected and fall back to bar chart when category count exceeds 7."""
    rows = [
        {"ward": f"Ward {i}", "grants": 100000.0}
        for i in range(1, 10)  # 9 categories
    ]
    plan = AnalysisPlan(
        table_name="civic_grants",
        operation="sum",
        target_column="amount",
        group_by=["ward"],
    )
    config = ChartGenerator.generate(
        columns=["ward", "grants"],
        rows=rows,
        table_name="civic_grants",
        plan=plan,
    )

    # Must fall back to bar because 9 slices is cluttered
    assert config.chart_type == "bar"
    assert config.x_key == "ward"


def test_pie_chart_rejected_when_negative_or_zero_values():
    """Pie chart must not be selected if any value is <= 0."""
    rows = [
        {"category": "Positive Share", "net_balance": 50000.0},
        {"category": "Deficit Share", "net_balance": -15000.0},
        {"category": "Breakeven", "net_balance": 0.0},
    ]
    plan = AnalysisPlan(
        table_name="budget_balances",
        operation="sum",
        target_column="net_balance",
        group_by=["category"],
    )
    config = ChartGenerator.generate(
        columns=["category", "net_balance"],
        rows=rows,
        table_name="budget_balances",
        plan=plan,
    )

    assert config.chart_type == "bar"


def test_pie_chart_rejected_for_average_operation():
    """Pie chart must not be used for average calculations because averages do not sum to 100%."""
    rows = [
        {"department": "Parks", "avg_salary": 65000.0},
        {"department": "Transit", "avg_salary": 72000.0},
        {"department": "Library", "avg_salary": 58000.0},
    ]
    plan = AnalysisPlan(
        table_name="dept_salaries",
        operation="average",
        target_column="salary",
        group_by=["department"],
    )
    config = ChartGenerator.generate(
        columns=["department", "avg_salary"],
        rows=rows,
        table_name="dept_salaries",
        plan=plan,
    )

    assert config.chart_type == "bar"


def test_table_selected_for_non_numeric_data():
    """Results with no numeric metrics must select table view."""
    rows = [
        {"vendor": "Acme Corp", "category": "Construction", "status": "Active"},
        {"vendor": "Global Tech", "category": "IT", "status": "Pending"},
    ]
    config = ChartGenerator.generate(
        columns=["vendor", "category", "status"],
        rows=rows,
        table_name="vendor_contracts",
    )
    assert config.chart_type == "table"
    assert "no numeric metrics" in config.selection_reason.lower()


def test_table_selected_for_high_cardinality():
    """Results with > 30 items must select table view to prevent illegible charts."""
    rows = [{"id": f"ID_{i}", "val": i * 10} for i in range(45)]
    config = ChartGenerator.generate(
        columns=["id", "val"],
        rows=rows,
        table_name="large_table",
    )
    assert config.chart_type == "table"
    assert "cardinality" in config.selection_reason.lower()


def test_table_selected_for_single_scalar():
    """Single scalar calculations (1 row, 1 col) default to table summary."""
    rows = [{"total_count": 42}]
    config = ChartGenerator.generate(
        columns=["total_count"],
        rows=rows,
        table_name="dept_expenses",
    )
    assert config.chart_type == "table"
    assert "scalar" in config.selection_reason.lower()


def test_format_detection():
    """Test format detection for currency, percent, and count."""
    rows = [
        {
            "dept": "Health",
            "spending_amount": 100000.0,
            "unemployment_rate": 5.2,
            "record_count": 14,
        }
    ]
    config = ChartGenerator.generate(
        columns=["dept", "spending_amount", "unemployment_rate", "record_count"],
        rows=rows,
        table_name="dept_stats",
    )
    series_map = {s.key: s.format_type for s in config.series}
    assert series_map["spending_amount"] == "currency"
    assert series_map["unemployment_rate"] == "percent"
    assert series_map["record_count"] == "integer"


def test_analytics_service_attaches_chart():
    """Analytics service end-to-end execution must populate chart config on AnalyticalResult."""
    req = AnalyticalQueryRequest(
        question="What is the total expenditure by department?",
        table_name="dept_expenses",
    )
    res = analytics_service.run_analytical_query(req)
    assert res.chart is not None
    assert res.chart.chart_type in ("bar", "pie", "line", "table")
    assert res.chart.x_key is not None
    assert len(res.chart.data) == res.row_count

    # Check calculation item transformation preserves chart
    calc = analytics_service.to_calculation_item(res)
    assert calc.chart is not None
    assert calc.chart.chart_type == res.chart.chart_type


def test_api_visualize_endpoint(client):
    """POST /api/v1/analytics/visualize must return a valid ChartConfig."""
    res_payload = {
        "plan": {
            "table_name": "dept_expenses",
            "operation": "sum",
            "target_column": "amount",
            "group_by": ["department"],
            "filters": [],
            "sort_by": [],
            "limit": 10,
        },
        "query_sql": "SELECT department, SUM(amount) AS total_amount FROM dept_expenses GROUP BY department",
        "columns": ["department", "total_amount"],
        "rows": [
            {"department": "Parks", "total_amount": 1000.0},
            {"department": "Library", "total_amount": 500.0},
            {"department": "Transit", "total_amount": 2000.0},
        ],
        "row_count": 3,
        "rows_scanned": 150,
        "execution_time_ms": 1.2,
        "table_name": "dept_expenses",
        "derivation": "Sum of amount by department",
    }

    response = client.post("/api/v1/analytics/visualize", json=res_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["chart_type"] == "pie"  # 3 positive slices with sum
    assert data["x_key"] == "department"
    assert len(data["series"]) == 1
    assert data["is_empty"] is False


def test_orchestration_query_includes_chart():
    """Natural language query routed to data_analysis must populate chart in QueryResponse."""
    orchestrator = QueryOrchestrator()
    req = QueryRequest(
        question="What is the total expenditure by department?",
        include_calculations=True,
    )
    resp = orchestrator.orchestrate(req)
    assert resp.calculation is not None
    assert resp.calculation.chart is not None
    assert resp.chart is not None
    assert resp.chart.chart_type in ("bar", "pie", "line", "table")
    assert len(resp.chart.data) > 0
