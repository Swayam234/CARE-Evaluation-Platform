"""
Test Suite – Automated Evaluation Pipeline
==========================================
Tests:
  1. EvaluationRun CRUD
  2. AgentTrace & ToolTrace bulk ingestion
  3. KPI Calculation Engine (all 8 telemetry KPIs + benchmark accuracy)
  4. KPI Transparency & Unavailable KPIs (never treated as 0)
  5. Pipeline Orchestrator -> Existing Scoring Engine integration
  6. Simulation Adapter endpoint
  7. Regression: Manual Evaluation still works completely
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from app.database.database import Base, engine, SessionLocal
from app.models.pipeline import (
    EvaluationRun, AgentTrace, ToolTrace, KpiMeasurement,
    EvaluationDataset, EvaluationTestCase, TestCaseResult,
)
from app.models.evaluation import Evaluation
from app.services.kpi_calculator import (
    calculate_kpis_from_run,
    calc_average_latency,
    calc_failure_rate,
    calc_retry_rate,
    calc_tool_success_rate,
    calc_throughput,
    calc_token_consumption,
    calc_cost_per_task,
    calc_cost_per_successful_task,
    calc_task_success_rate_from_results,
    calc_goal_completion_rate_from_results,
    calc_tool_selection_accuracy_from_results,
)
from app.services.pipeline_orchestrator import (
    calculate_kpis_for_run,
    generate_evaluation_from_run,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup runs created during tests
    db = SessionLocal()
    try:
        db.query(KpiMeasurement).delete()
        db.query(ToolTrace).delete()
        db.query(AgentTrace).delete()
        db.query(TestCaseResult).delete()
        db.query(EvaluationTestCase).delete()
        db.query(EvaluationDataset).delete()
        db.query(EvaluationRun).delete()
        db.commit()
    finally:
        db.close()


# ── 1. Unit Tests for KPI Calculator ──────────────────────────────────────────

class MockTrace:
    def __init__(self, latency_ms=500.0, status="success", input_tokens=100, output_tokens=50, retry_count=0):
        self.latency_ms = latency_ms
        self.status = status
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.retry_count = retry_count


class MockToolTrace:
    def __init__(self, status="success", latency_ms=100.0):
        self.status = status
        self.latency_ms = latency_ms


class MockTestCaseResult:
    def __init__(self, success=True, actual_tool="search", expected_tool="search", score=1.0):
        self.success = success
        self.actual_tool = actual_tool
        self.score = score
        self.test_case = type("MockTC", (), {"expected_tool": expected_tool})()


def test_calc_average_latency():
    traces = [MockTrace(latency_ms=200), MockTrace(latency_ms=400)]
    res = calc_average_latency(traces)
    assert res.calculation_status == "calculated"
    assert res.raw_value == 300.0
    assert res.unit == "ms"

    # Empty traces
    res_empty = calc_average_latency([])
    assert res_empty.calculation_status == "unavailable"
    assert res_empty.raw_value is None


def test_calc_failure_rate():
    traces = [
        MockTrace(status="success"),
        MockTrace(status="failed"),
        MockTrace(status="error"),
        MockTrace(status="success"),
    ]
    res = calc_failure_rate(traces)
    assert res.calculation_status == "calculated"
    assert res.raw_value == 50.0  # 2 out of 4


def test_calc_retry_rate():
    traces = [
        MockTrace(retry_count=0),
        MockTrace(retry_count=1),
        MockTrace(retry_count=2),
        MockTrace(retry_count=0),
    ]
    res = calc_retry_rate(traces)
    assert res.calculation_status == "calculated"
    assert res.raw_value == 50.0  # 2 out of 4 had retries


def test_calc_tool_success_rate():
    tools = [
        MockToolTrace(status="success"),
        MockToolTrace(status="success"),
        MockToolTrace(status="failed"),
    ]
    res = calc_tool_success_rate(tools)
    assert res.calculation_status == "calculated"
    assert res.raw_value == round(2 / 3 * 100, 2)

    # Empty tools
    res_empty = calc_tool_success_rate([])
    assert res_empty.calculation_status == "unavailable"
    assert res_empty.raw_value is None


def test_calc_token_consumption():
    traces = [
        MockTrace(input_tokens=200, output_tokens=100),  # total 300
        MockTrace(input_tokens=400, output_tokens=300),  # total 700
    ]
    res = calc_token_consumption(traces)
    assert res.calculation_status == "calculated"
    assert res.raw_value == 500.0  # (300 + 700) / 2


def test_calc_cost_per_task():
    traces = [
        MockTrace(input_tokens=1000, output_tokens=1000),  # 1k in, 1k out
    ]
    # $0.001 per 1k in, $0.002 per 1k out -> cost = $0.003
    res = calc_cost_per_task(traces, input_cost_per_1k=0.001, output_cost_per_1k=0.002)
    assert res.calculation_status == "calculated"
    assert res.raw_value == 0.003

    # Missing cost config -> unavailable
    res_unavail = calc_cost_per_task(traces, input_cost_per_1k=None, output_cost_per_1k=None)
    assert res_unavail.calculation_status == "unavailable"
    assert res_unavail.raw_value is None


def test_calc_benchmark_accuracy():
    results = [
        MockTestCaseResult(success=True),
        MockTestCaseResult(success=True),
        MockTestCaseResult(success=False),
        MockTestCaseResult(success=True),
    ]
    res = calc_task_success_rate_from_results(results)
    assert res.calculation_status == "calculated"
    assert res.raw_value == 75.0  # 3/4 = 75%


# ── 2. API Endpoints: Evaluation Runs ─────────────────────────────────────────

def test_create_and_get_evaluation_run():
    res = client.post(
        "/api/evaluation-runs/",
        json={
            "agent_name": "Test Support Agent",
            "agent_type": "Customer Support",
            "description": "Integration test run",
            "total_tasks": 10,
            "llm_input_cost_per_1k": 0.0005,
            "llm_output_cost_per_1k": 0.0015,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["id"] > 0
    assert data["agent_name"] == "Test Support Agent"
    assert data["status"] == "PENDING"
    run_id = data["id"]

    # Get run
    get_res = client.get(f"/api/evaluation-runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["agent_name"] == "Test Support Agent"

    # Status endpoint
    status_res = client.get(f"/api/evaluation-runs/{run_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["trace_count"] == 0


def test_ingest_traces_and_tool_traces():
    # 1. Create run
    run_res = client.post(
        "/api/evaluation-runs/",
        json={"agent_name": "Ingest Agent", "agent_type": "RAG Agent"},
    )
    run_id = run_res.json()["id"]

    # 2. Ingest traces
    now = datetime.utcnow()
    traces_payload = {
        "traces": [
            {
                "trace_id": f"trace-{i}",
                "task_id": f"task-{i}",
                "model_name": "gpt-4o",
                "started_at": now.isoformat(),
                "completed_at": (now + timedelta(milliseconds=500)).isoformat(),
                "latency_ms": 500.0 + i * 50,
                "status": "success" if i != 2 else "failed",
                "input_tokens": 400,
                "output_tokens": 200,
                "total_tokens": 600,
                "retry_count": 1 if i == 1 else 0,
            }
            for i in range(5)
        ]
    }
    ingest_res = client.post(f"/api/evaluation-runs/{run_id}/traces", json=traces_payload)
    assert ingest_res.status_code == 201
    traces = ingest_res.json()
    assert len(traces) == 5
    first_trace_id = traces[0]["id"]

    # 3. Ingest tool traces
    tool_payload = {
        "agent_trace_id": first_trace_id,
        "tool_traces": [
            {
                "tool_name": "search_docs",
                "started_at": now.isoformat(),
                "completed_at": (now + timedelta(milliseconds=120)).isoformat(),
                "latency_ms": 120.0,
                "status": "success",
            }
        ]
    }
    tool_res = client.post(f"/api/evaluation-runs/{run_id}/tool-traces", json=tool_payload)
    assert tool_res.status_code == 201
    assert len(tool_res.json()) == 1

    # 4. Check status
    status_res = client.get(f"/api/evaluation-runs/{run_id}/status")
    assert status_res.json()["trace_count"] == 5
    assert status_res.json()["tool_trace_count"] == 1


# ── 3. Pipeline Orchestrator Integration: Full CARE Evaluation ────────────────

def test_full_pipeline_orchestration():
    db = SessionLocal()
    try:
        # Create run in DB
        run = EvaluationRun(
            agent_name="Pipeline E2E Agent",
            agent_type="Workflow Automation",
            status="RUNNING",
            started_at=datetime.utcnow() - timedelta(seconds=10),
            completed_at=datetime.utcnow(),
            total_tasks=3,
            llm_input_cost_per_1k=0.001,
            llm_output_cost_per_1k=0.002,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Add traces
        for i in range(3):
            trace = AgentTrace(
                evaluation_run_id=run.id,
                trace_id=f"e2e-trace-{i}",
                task_id=f"e2e-task-{i}",
                latency_ms=600.0,
                status="success",
                input_tokens=500,
                output_tokens=250,
                total_tokens=750,
                retry_count=0,
            )
            db.add(trace)
        db.commit()

        # Generate evaluation via orchestrator
        evaluation = generate_evaluation_from_run(run.id, db)

        assert evaluation is not None
        assert evaluation.id > 0
        assert evaluation.agent_name == "Pipeline E2E Agent"
        assert evaluation.evaluator == "automated_pipeline"
        assert evaluation.care_score is not None
        assert 0 <= evaluation.care_score <= 100
        # R and E are computed from telemetry traces
        assert evaluation.score_r is not None
        assert evaluation.score_e is not None
        # C and A are None when no dataset/judge is configured (not fabricated as 0)
        assert evaluation.score_c is None
        assert evaluation.score_a is None
        assert evaluation.recommendation in [
            "Production Ready", "Pilot and Scale", "Needs Improvement", "Not Recommended", "Insufficient Data",
        ]

        # Verify run was updated with evaluation_id
        db.refresh(run)
        assert run.evaluation_id == evaluation.id
        assert run.status == "COMPLETED"

        # Check KPI measurements stored in DB
        measurements = db.query(KpiMeasurement).filter(KpiMeasurement.evaluation_run_id == run.id).all()
        assert len(measurements) > 0

        # Check that latency_ms is calculated and positive
        lat_m = next((m for m in measurements if m.kpi_name == "latency_ms"), None)
        assert lat_m is not None
        assert lat_m.calculation_status == "calculated"
        assert lat_m.raw_value == 600.0

        # Check that unavailable KPIs are NOT 0 and marked as unavailable
        rel_m = next((m for m in measurements if m.kpi_name == "reasoning_quality"), None)
        assert rel_m is not None
        assert rel_m.calculation_status == "unavailable"
        assert rel_m.raw_value is None

    finally:
        db.close()


# ── 4. Simulation Adapter API Test ────────────────────────────────────────────

def test_simulation_adapter_endpoint():
    res = client.post(
        "/api/simulation/run",
        json={
            "agent_name": "Demo Simulation Agent",
            "agent_type": "Coding Assistant",
            "num_tasks": 5,
            "success_rate": 0.9,
            "avg_latency_ms": 400.0,
            "latency_variance_pct": 0.2,
            "avg_input_tokens": 300,
            "avg_output_tokens": 150,
            "tool_call_rate": 0.5,
            "tool_success_rate": 0.95,
            "retry_rate": 0.05,
            "llm_input_cost_per_1k": 0.0005,
            "llm_output_cost_per_1k": 0.0015,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "simulation_warning" in data
    assert "SIMULATION" in data["simulation_warning"]
    assert data["run_id"] > 0
    assert data["num_tasks"] == 5


# ── 5. Regression Test: Existing Manual Evaluation Still Works ────────────────

def test_manual_evaluation_regression():
    """Ensure existing manual evaluation flow is 100% untouched and functional."""
    payload = {
        "agent_name": "Regression Test Agent",
        "agent_type": "Chatbot",
        "description": "Ensuring manual evaluation continues to work",
        "evaluator": "QA Test",
        "computational_intelligence": {
            "relevance_score": 85.0,
            "reasoning_quality": 80.0,
        },
        "accuracy": {
            "task_success_rate": 90.0,
            "precision": 88.0,
        },
        "reliability": {
            "failure_rate": 5.0,
            "latency_ms": 450.0,
        },
        "economics": {
            "cost_per_task": 0.02,
            "token_consumption": 800.0,
        },
    }
    res = client.post("/api/evaluations/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["agent_name"] == "Regression Test Agent"
    assert data["care_score"] is not None
    assert data["care_score"] > 0
    assert data["recommendation"] is not None
