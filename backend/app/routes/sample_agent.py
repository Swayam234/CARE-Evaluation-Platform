"""
Sample Agent – Simulation Adapter
==================================

⚠️  SIMULATION ONLY ⚠️
This module simulates an AI agent execution for demonstration and testing purposes.
It generates SYNTHETIC traces – these are NOT real agent executions.
The simulation is clearly labeled in all output and trace metadata.

Architecture intent:
  - This is an ADAPTER, not a real agent.
  - A real AI agent would ingest traces via POST /api/evaluation-runs/{id}/traces.
  - This adapter calls those same endpoints internally, demonstrating the exact
    integration path a real agent would use.
  - Replace or supplement this adapter with a real agent integration
    by following the same trace ingestion pattern.

Label conventions:
  - All generated traces include raw_metadata.simulation=True
  - All EvaluationRun descriptions include "[SIMULATION]"
  - The API response includes a 'simulation_warning' field
"""
import random
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.pipeline import (
    EvaluationRun, AgentTrace, ToolTrace, TestCaseResult, EvaluationTestCase,
)
from app.schemas.pipeline import SimulationConfig
from app.services.pipeline_orchestrator import generate_evaluation_from_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulation", tags=["Simulation Adapter (Demo Only)"])

# ── Simulation constants ──────────────────────────────────────────────────────
SIMULATED_TOOLS = ["search_web", "read_document", "summarize", "send_email", "query_db", "calculate"]
SIMULATED_MODELS = ["gpt-4o", "gemini-1.5-pro", "claude-3-5-sonnet", "llama-3.1-70b"]


def _simulate_traces(
    run: EvaluationRun,
    config: SimulationConfig,
    db: Session,
) -> List[AgentTrace]:
    """
    Generate synthetic agent execution traces.
    Clearly labeled as simulation in all metadata.
    """
    traces = []
    run_start = datetime.utcnow()
    model = random.choice(SIMULATED_MODELS)

    for task_num in range(config.num_tasks):
        task_id = f"sim-task-{run.id}-{task_num:04d}"

        # Simulate latency with variance
        variance = config.avg_latency_ms * config.latency_variance_pct
        latency = max(10.0, random.gauss(config.avg_latency_ms, variance))

        # Simulate success/failure
        has_retry = random.random() < config.retry_rate
        task_failed = random.random() > config.success_rate
        task_status = "failed" if task_failed else "success"

        # Simulate token usage
        input_tokens = max(1, int(random.gauss(config.avg_input_tokens, config.avg_input_tokens * 0.2)))
        output_tokens = max(1, int(random.gauss(config.avg_output_tokens, config.avg_output_tokens * 0.2)))
        total_tokens = input_tokens + output_tokens

        task_start = run_start + timedelta(seconds=task_num * (latency / 1000.0 + 0.1))
        task_end = task_start + timedelta(milliseconds=latency)

        trace = AgentTrace(
            evaluation_run_id=run.id,
            trace_id=f"sim-trace-{run.id}-{task_num:04d}",
            task_id=task_id,
            model_name=model,
            started_at=task_start,
            completed_at=task_end,
            latency_ms=round(latency, 2),
            status=task_status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            error_message=f"Simulated error for task {task_num}" if task_failed else None,
            retry_count=1 if has_retry else 0,
            raw_metadata={
                "simulation": True,
                "simulation_label": config.simulation_label,
                "task_number": task_num,
                "model": model,
            },
        )
        db.add(trace)
        traces.append(trace)

    db.commit()
    for t in traces:
        db.refresh(t)

    logger.info("Simulated %d agent traces for run %d", len(traces), run.id)
    return traces


def _simulate_tool_traces(
    run: EvaluationRun,
    agent_traces: List[AgentTrace],
    config: SimulationConfig,
    db: Session,
) -> None:
    """Generate synthetic tool call traces for tasks that use tools."""
    tool_count = 0
    for trace in agent_traces:
        if random.random() > config.tool_call_rate:
            continue
        # Simulate 1-3 tool calls per task
        num_tools = random.randint(1, 3)
        tools_used = random.sample(SIMULATED_TOOLS, min(num_tools, len(SIMULATED_TOOLS)))

        for tool_name in tools_used:
            tool_latency = random.uniform(50, 500)
            tool_failed = random.random() > config.tool_success_rate
            tool_status = "failed" if tool_failed else "success"

            tool_trace = ToolTrace(
                agent_trace_id=trace.id,
                trace_id=trace.trace_id,
                tool_name=tool_name,
                started_at=trace.started_at,
                completed_at=trace.started_at + timedelta(milliseconds=tool_latency) if trace.started_at else None,
                latency_ms=round(tool_latency, 2),
                status=tool_status,
                error_message=f"Simulated tool error" if tool_failed else None,
                raw_metadata={"simulation": True},
            )
            db.add(tool_trace)
            tool_count += 1

    db.commit()
    logger.info("Simulated %d tool traces for run %d", tool_count, run.id)


def _simulate_test_case_results(
    run: EvaluationRun,
    agent_traces: List[AgentTrace],
    config: SimulationConfig,
    db: Session,
) -> None:
    """
    If a dataset is attached, generate simulated test case results.
    Results use exact-match evaluator with simulated success/failure.
    """
    if not config.dataset_id:
        return

    test_cases = (
        db.query(EvaluationTestCase)
        .filter(EvaluationTestCase.dataset_id == config.dataset_id)
        .all()
    )
    if not test_cases:
        return

    # Match test cases to traces by index
    for i, tc in enumerate(test_cases):
        if i >= len(agent_traces):
            break
        trace = agent_traces[i]
        success = random.random() < config.success_rate

        # Simulate tool selection
        actual_tool = None
        if tc.expected_tool:
            actual_tool = tc.expected_tool if random.random() < 0.85 else random.choice(SIMULATED_TOOLS)

        result = TestCaseResult(
            evaluation_run_id=run.id,
            test_case_id=tc.id,
            actual_output=(
                tc.expected_output if success else f"Simulated incorrect output for task {i}"
            ),
            actual_tool=actual_tool,
            success=success,
            evaluator_used="simulation_exact_match",
            score=1.0 if success else 0.0,
            notes="Simulated result – not a real evaluation",
        )
        db.add(result)

    db.commit()
    logger.info("Simulated test case results for dataset %d in run %d", config.dataset_id, run.id)


def _run_full_simulation(run_id: int, config: SimulationConfig) -> None:
    """
    Background task: run the complete simulation and generate a CARE evaluation.
    Clearly labeled as simulation throughout.
    """
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            logger.error("Simulation: run %d not found", run_id)
            return

        run.status = "RUNNING"
        run.started_at = datetime.utcnow()
        db.commit()

        # 1. Simulate agent traces
        agent_traces = _simulate_traces(run, config, db)

        # 2. Simulate tool traces
        _simulate_tool_traces(run, agent_traces, config, db)

        # 3. Simulate test case results (if dataset attached)
        _simulate_test_case_results(run, agent_traces, config, db)

        # 4. Mark run as completed
        run.status = "COMPLETED"
        run.completed_at = datetime.utcnow()
        run.total_tasks = config.num_tasks
        db.commit()

        # 5. Generate CARE evaluation via existing pipeline
        generate_evaluation_from_run(run_id, db)

        logger.info("Simulation complete for run %d – evaluation generated", run_id)

    except Exception as exc:
        logger.error("Simulation failed for run %d: %s", run_id, exc)
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if run:
            run.status = "FAILED"
            run.error_message = f"Simulation error: {exc}"
            db.commit()
    finally:
        db.close()


# ── API Endpoint ──────────────────────────────────────────────────────────────

@router.post("/run")
def start_simulation(
    config: SimulationConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a simulated evaluation run.

    ⚠️  SIMULATION ONLY – generates synthetic traces.
    This endpoint is for demonstration and testing purposes only.
    For real AI agents, use POST /api/evaluation-runs/{id}/traces instead.

    The simulation:
    1. Creates an EvaluationRun
    2. Generates synthetic AgentTrace records
    3. Generates synthetic ToolTrace records
    4. (Optional) Generates TestCaseResults if dataset_id is provided
    5. Runs the full CARE pipeline → generates CARE Score
    6. Returns immediately; poll /api/evaluation-runs/{id}/status for completion

    All traces are labeled with simulation=True in metadata.
    """
    description = (
        f"[SIMULATION] {config.description or ''} | "
        f"Synthetic {config.num_tasks} tasks @ {config.avg_latency_ms}ms avg latency | "
        f"Success rate: {config.success_rate * 100:.0f}%"
    )

    run = EvaluationRun(
        agent_name=config.agent_name,
        agent_type=config.agent_type,
        description=description,
        dataset_name=config.dataset_name if hasattr(config, 'dataset_name') else None,
        dataset_id=config.dataset_id,
        total_tasks=config.num_tasks,
        status="PENDING",
        llm_input_cost_per_1k=config.llm_input_cost_per_1k,
        llm_output_cost_per_1k=config.llm_output_cost_per_1k,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_run_full_simulation, run.id, config)

    return {
        "simulation_warning": (
            "⚠️ SIMULATION MODE: This run uses SYNTHETIC traces. "
            "Results are for demonstration purposes only, not real agent performance."
        ),
        "run_id": run.id,
        "agent_name": run.agent_name,
        "num_tasks": config.num_tasks,
        "status": "PENDING",
        "poll_url": f"/api/evaluation-runs/{run.id}/status",
        "message": f"Simulation started. Poll the status endpoint to track progress.",
    }
