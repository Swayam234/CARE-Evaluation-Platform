"""
Pipeline API Routes
===================
REST endpoints for the automated evaluation pipeline.

All new endpoints live under /api/evaluation-runs.
Existing /api/evaluations endpoints are not modified.

Async pattern: long-running operations (calculate-kpis, generate-evaluation)
run via FastAPI BackgroundTasks to avoid blocking the HTTP response.
Status is polled via GET /{run_id}/status.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.pipeline import (
    EvaluationRun, AgentTrace, ToolTrace, KpiMeasurement, TestCaseResult,
)
from app.schemas.pipeline import (
    EvaluationRunCreate, EvaluationRunRead, EvaluationRunSummary,
    AgentTraceRead, AgentTraceBulkCreate,
    ToolTraceBulkCreate, ToolTraceRead,
    KpiMeasurementRead, KpiCalculationResponse, KpiCoverageStats,
    GenerateEvaluationResponse, RunStatusResponse,
    TestCaseResultBulkCreate, TestCaseResultRead,
)
from app.services.pipeline_orchestrator import (
    calculate_kpis_for_run, generate_evaluation_from_run,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluation-runs", tags=["Automated Evaluation Pipeline"])


# ── Background task wrappers ──────────────────────────────────────────────────

def _bg_calculate_kpis(run_id: int, db_session_factory) -> None:
    """Background task: calculate KPIs and persist measurements."""
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if run:
            run.status = "RUNNING"
            db.commit()
        calculate_kpis_for_run(run_id, db)
    except Exception as exc:
        logger.error("Background KPI calculation failed for run %d: %s", run_id, exc)
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if run:
            run.status = "FAILED"
            run.error_message = str(exc)
            db.commit()
    finally:
        db.close()


def _bg_generate_evaluation(run_id: int) -> None:
    """Background task: calculate KPIs + generate CARE evaluation."""
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if run and run.status == "PENDING":
            run.status = "RUNNING"
            db.commit()
        generate_evaluation_from_run(run_id, db)
    except Exception as exc:
        logger.error("Background evaluation generation failed for run %d: %s", run_id, exc)
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if run:
            run.status = "FAILED"
            run.error_message = str(exc)
            db.commit()
    finally:
        db.close()


# ── Evaluation Run CRUD ───────────────────────────────────────────────────────

@router.post("/", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED)
def create_evaluation_run(data: EvaluationRunCreate, db: Session = Depends(get_db)):
    """Create a new Evaluation Run in PENDING status."""
    run = EvaluationRun(
        agent_name=data.agent_name,
        agent_type=data.agent_type,
        description=data.description,
        dataset_name=data.dataset_name,
        dataset_id=data.dataset_id,
        total_tasks=data.total_tasks,
        status="PENDING",
        llm_input_cost_per_1k=data.llm_input_cost_per_1k,
        llm_output_cost_per_1k=data.llm_output_cost_per_1k,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    logger.info("Created evaluation run %d for agent '%s'", run.id, run.agent_name)
    return run


@router.get("/", response_model=List[EvaluationRunSummary])
def list_evaluation_runs(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all Evaluation Runs with optional status filter."""
    query = db.query(EvaluationRun)
    if status_filter:
        query = query.filter(EvaluationRun.status == status_filter.upper())
    return query.order_by(EvaluationRun.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{run_id}", response_model=EvaluationRunRead)
def get_evaluation_run(run_id: int, db: Session = Depends(get_db)):
    """Get a single Evaluation Run by ID."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    return run


@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: int, db: Session = Depends(get_db)):
    """
    Poll the status of an Evaluation Run.
    Frontend uses this endpoint to implement async progress tracking.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")

    trace_count = db.query(AgentTrace).filter(AgentTrace.evaluation_run_id == run_id).count()
    tool_trace_count = (
        db.query(ToolTrace)
        .join(AgentTrace, ToolTrace.agent_trace_id == AgentTrace.id)
        .filter(AgentTrace.evaluation_run_id == run_id)
        .count()
    )
    return RunStatusResponse(
        run_id=run.id,
        status=run.status,
        agent_name=run.agent_name,
        total_tasks=run.total_tasks,
        trace_count=trace_count,
        tool_trace_count=tool_trace_count,
        started_at=run.started_at,
        completed_at=run.completed_at,
        evaluation_id=run.evaluation_id,
        error_message=run.error_message,
    )


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation_run(run_id: int, db: Session = Depends(get_db)):
    """Delete an Evaluation Run and all associated data."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    db.delete(run)
    db.commit()


# ── Trace Ingestion ───────────────────────────────────────────────────────────

@router.post("/{run_id}/traces", response_model=List[AgentTraceRead], status_code=status.HTTP_201_CREATED)
def ingest_agent_traces(run_id: int, payload: AgentTraceBulkCreate, db: Session = Depends(get_db)):
    """
    Ingest agent execution traces for a run.
    Accepts bulk payloads (up to 1000 traces per request).
    Maps OpenTelemetry span attributes to AgentTrace fields.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    if run.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Cannot add traces to a COMPLETED run")

    # Set run to RUNNING when first traces arrive
    if run.status == "PENDING":
        run.status = "RUNNING"
        run.started_at = run.started_at or datetime.utcnow()

    created = []
    for t in payload.traces:
        trace = AgentTrace(
            evaluation_run_id=run_id,
            trace_id=t.trace_id,
            task_id=t.task_id,
            model_name=t.model_name,
            started_at=t.started_at,
            completed_at=t.completed_at,
            latency_ms=t.latency_ms,
            status=t.status.value,
            input_tokens=t.input_tokens,
            output_tokens=t.output_tokens,
            total_tokens=t.total_tokens,
            error_message=t.error_message,
            retry_count=t.retry_count,
            raw_metadata=t.raw_metadata,
        )
        db.add(trace)
        created.append(trace)

    db.commit()
    for trace in created:
        db.refresh(trace)

    logger.info("Ingested %d traces for run %d", len(created), run_id)
    return created


@router.post("/{run_id}/tool-traces", response_model=List[ToolTraceRead], status_code=status.HTTP_201_CREATED)
def ingest_tool_traces(run_id: int, payload: ToolTraceBulkCreate, db: Session = Depends(get_db)):
    """
    Ingest tool call traces, linked to a specific agent trace by agent_trace_id.
    """
    # Verify parent agent trace belongs to this run
    parent = db.query(AgentTrace).filter(
        AgentTrace.id == payload.agent_trace_id,
        AgentTrace.evaluation_run_id == run_id,
    ).first()
    if not parent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent trace {payload.agent_trace_id} not found in run {run_id}",
        )

    created = []
    for t in payload.tool_traces:
        tool_trace = ToolTrace(
            agent_trace_id=payload.agent_trace_id,
            trace_id=t.trace_id,
            tool_name=t.tool_name,
            started_at=t.started_at,
            completed_at=t.completed_at,
            latency_ms=t.latency_ms,
            status=t.status.value,
            error_message=t.error_message,
            raw_metadata=t.raw_metadata,
        )
        db.add(tool_trace)
        created.append(tool_trace)

    db.commit()
    for tt in created:
        db.refresh(tt)

    return created


@router.get("/{run_id}/traces", response_model=List[AgentTraceRead])
def get_run_traces(
    run_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get agent traces for a run (paginated)."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    return (
        db.query(AgentTrace)
        .filter(AgentTrace.evaluation_run_id == run_id)
        .order_by(AgentTrace.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Test Case Results ─────────────────────────────────────────────────────────

@router.post("/{run_id}/test-case-results", response_model=List[TestCaseResultRead], status_code=status.HTTP_201_CREATED)
def submit_test_case_results(run_id: int, payload: TestCaseResultBulkCreate, db: Session = Depends(get_db)):
    """Submit benchmark test case results for a run."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")

    created = []
    for r in payload.results:
        result = TestCaseResult(
            evaluation_run_id=run_id,
            test_case_id=r.test_case_id,
            actual_output=r.actual_output,
            actual_tool=r.actual_tool,
            success=r.success,
            evaluator_used=r.evaluator_used,
            score=r.score,
            notes=r.notes,
        )
        db.add(result)
        created.append(result)

    db.commit()
    for r in created:
        db.refresh(r)

    return created


# ── Mark Run Complete ─────────────────────────────────────────────────────────

@router.post("/{run_id}/complete", response_model=EvaluationRunRead)
def mark_run_complete(run_id: int, db: Session = Depends(get_db)):
    """
    Mark an Evaluation Run as COMPLETED.
    Call this after all traces and test-case results have been ingested.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    if run.status == "FAILED":
        raise HTTPException(status_code=400, detail="Cannot complete a FAILED run")

    trace_count = db.query(AgentTrace).filter(AgentTrace.evaluation_run_id == run_id).count()
    if trace_count == 0:
        raise HTTPException(status_code=400, detail="Cannot complete a run with no traces")

    run.status = "COMPLETED"
    run.completed_at = run.completed_at or datetime.utcnow()
    run.total_tasks = run.total_tasks or trace_count
    db.commit()
    db.refresh(run)
    return run


# ── KPI Calculation ───────────────────────────────────────────────────────────

@router.post("/{run_id}/calculate-kpis")
def trigger_kpi_calculation(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger async KPI calculation for a run.
    Calculation runs in the background via FastAPI BackgroundTasks.
    Poll GET /{run_id}/kpis to see results once complete.

    Future: Replace BackgroundTasks with Celery/Redis for distributed execution.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    if run.status == "FAILED":
        raise HTTPException(status_code=400, detail="Cannot calculate KPIs for a FAILED run")

    background_tasks.add_task(_bg_calculate_kpis, run_id, None)
    return {
        "message": f"KPI calculation started for run {run_id}",
        "run_id": run_id,
        "poll_url": f"/api/evaluation-runs/{run_id}/kpis",
    }


@router.get("/{run_id}/kpis", response_model=KpiCalculationResponse)
def get_run_kpis(run_id: int, db: Session = Depends(get_db)):
    """
    Get all KPI measurements for a run.
    Each measurement includes source and calculation_status for full transparency.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")

    measurements = (
        db.query(KpiMeasurement)
        .filter(KpiMeasurement.evaluation_run_id == run_id)
        .order_by(KpiMeasurement.kpi_name)
        .all()
    )

    total = len(measurements)
    calculated = sum(1 for m in measurements if m.calculation_status == "calculated")
    unavailable = sum(1 for m in measurements if m.calculation_status == "unavailable")
    error = sum(1 for m in measurements if m.calculation_status == "error")

    coverage = KpiCoverageStats(
        total_kpis=total,
        calculated=calculated,
        unavailable=unavailable,
        error=error,
        coverage_percent=round(calculated / total * 100, 1) if total > 0 else 0.0,
    )

    msg = f"{calculated}/{total} KPIs calculated" if total > 0 else "No KPIs calculated yet"

    return KpiCalculationResponse(
        run_id=run_id,
        measurements=[KpiMeasurementRead.model_validate(m) for m in measurements],
        coverage=coverage,
        message=msg,
    )


# ── Generate CARE Evaluation ──────────────────────────────────────────────────

@router.post("/{run_id}/generate-evaluation")
def generate_care_evaluation(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger async generation of a full CARE evaluation from an Evaluation Run.

    Full async pipeline:
      Traces → KPI Calculator → Existing CARE Scoring Engine → Existing Recommendation Engine → Evaluation

    The resulting Evaluation record is identical to a manual evaluation and
    can be viewed on the existing /results/{id} page.

    Poll GET /{run_id}/status to check when evaluation_id is set (indicating completion).
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    if run.status == "FAILED":
        raise HTTPException(status_code=400, detail="Cannot generate evaluation for a FAILED run")

    trace_count = db.query(AgentTrace).filter(AgentTrace.evaluation_run_id == run_id).count()
    if trace_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No traces found for this run. Ingest traces before generating an evaluation.",
        )

    # Mark as RUNNING if still PENDING
    if run.status == "PENDING":
        run.status = "RUNNING"
        run.started_at = run.started_at or datetime.utcnow()
        db.commit()

    background_tasks.add_task(_bg_generate_evaluation, run_id)

    return {
        "message": f"Evaluation generation started for run {run_id}",
        "run_id": run_id,
        "poll_url": f"/api/evaluation-runs/{run_id}/status",
        "note": "Poll the status endpoint. When evaluation_id is set, the CARE evaluation is complete.",
    }
