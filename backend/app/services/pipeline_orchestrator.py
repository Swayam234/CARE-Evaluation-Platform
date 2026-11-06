"""
Pipeline Orchestrator
=====================
Orchestrates the full automated evaluation pipeline:

  Evaluation Run
      ↓
  AgentTraces + ToolTraces
      ↓
  KPI Calculator  (raw values, NO scoring)
      ↓
  Configured Evaluators
      ↓
  KpiMeasurement records
      ↓
  Map to EvaluationCreate  (existing schema)
      ↓
  Existing run_scoring()   (existing scoring engine – NOT duplicated)
      ↓
  Existing generate_recommendations()
      ↓
  Evaluation record saved

CRITICAL: This is the ONLY place that bridges automated KPIs to the
existing CARE scoring engine. It never modifies or duplicates scoring logic.
"""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.pipeline import (
    EvaluationRun, AgentTrace, ToolTrace,
    KpiMeasurement, TestCaseResult,
)
from app.models.evaluation import Evaluation, WeightConfig
from app.schemas.evaluation import (
    EvaluationCreate,
    ComputationalIntelligenceKPIs,
    AccuracyKPIs,
    ReliabilityKPIs,
    EconomicsKPIs,
    WeightConfigBase,
)
from app.schemas.pipeline import KpiCoverageStats
from app.services.kpi_calculator import calculate_kpis_from_run, RawKpiResult
from app.services.recommendations import generate_recommendations
from app.services.scoring import run_scoring
from app.services.evaluators.accuracy_evaluator import AccuracyEvaluator
from app.services.evaluators.tool_evaluator import ToolEvaluator
from app.services.evaluators.safety_evaluator import SafetyEvaluator
from app.services.evaluators.llm_judge import LlmJudge

logger = logging.getLogger(__name__)

# Registry of evaluators to run on every automated evaluation
_EVALUATORS = [
    AccuracyEvaluator(),
    ToolEvaluator(),
    SafetyEvaluator(),
    LlmJudge(),
]

# ── KPI name → EvaluationCreate field mapping ────────────────────────────────
# Maps kpi_name strings to the EvaluationCreate nested field paths.
# Only calculated KPIs will be mapped; unavailable ones remain None.

_KPI_TO_FIELD: dict = {
    # C – Computational Intelligence
    "relevance_score": ("computational_intelligence", "relevance_score"),
    "reasoning_quality": ("computational_intelligence", "reasoning_quality"),
    "completeness": ("computational_intelligence", "completeness"),
    "tool_selection_accuracy": ("computational_intelligence", "tool_selection_accuracy"),
    "planning_success_rate": ("computational_intelligence", "planning_success_rate"),
    "task_decomposition_accuracy": ("computational_intelligence", "task_decomposition_accuracy"),
    "recommendation_acceptance_rate": ("computational_intelligence", "recommendation_acceptance_rate"),
    # A – Accuracy
    "task_success_rate": ("accuracy", "task_success_rate"),
    "precision": ("accuracy", "precision"),
    "recall": ("accuracy", "recall"),
    "hallucination_rate": ("accuracy", "hallucination_rate"),
    "goal_completion_rate": ("accuracy", "goal_completion_rate"),
    # R – Reliability
    "failure_rate": ("reliability", "failure_rate"),
    "retry_rate": ("reliability", "retry_rate"),
    "tool_success_rate": ("reliability", "tool_success_rate"),
    "latency_ms": ("reliability", "latency_ms"),
    "consistency_score": ("reliability", "consistency_score"),
    "error_recovery_rate": ("reliability", "error_recovery_rate"),
    "safety_violation_rate": ("reliability", "safety_violation_rate"),
    "policy_compliance_score": ("reliability", "policy_compliance_score"),
    "audit_coverage": ("reliability", "audit_coverage"),
    "pii_leakage_rate": ("reliability", "pii_leakage_rate"),
    # E – Economics
    "cost_per_task": ("economics", "cost_per_task"),
    "token_consumption": ("economics", "token_consumption"),
    "throughput": ("economics", "throughput"),
    "resource_utilization": ("economics", "resource_utilization"),
    "human_effort_saved": ("economics", "human_effort_saved"),
    "productivity_improvement": ("economics", "productivity_improvement"),
    "business_roi": ("economics", "business_roi"),
    "payback_period_months": ("economics", "payback_period_months"),
    "cost_per_successful_task": ("economics", "cost_per_successful_task"),
}


def _get_active_weights(db: Session) -> WeightConfigBase:
    """Reuse the same weight-fetching logic as the evaluations router."""
    config = db.query(WeightConfig).filter(WeightConfig.id == 1).first()
    if not config:
        config = WeightConfig(id=1, weight_c=0.25, weight_a=0.30, weight_r=0.30, weight_e=0.15)
        db.add(config)
        db.commit()
        db.refresh(config)
    return WeightConfigBase(
        weight_c=config.weight_c,
        weight_a=config.weight_a,
        weight_r=config.weight_r,
        weight_e=config.weight_e,
    )


def _compute_kpi_coverage(measurements: list[RawKpiResult]) -> KpiCoverageStats:
    total = len(measurements)
    calculated = sum(1 for m in measurements if m.calculation_status == "calculated")
    unavailable = sum(1 for m in measurements if m.calculation_status == "unavailable")
    error = sum(1 for m in measurements if m.calculation_status == "error")
    coverage_pct = round(calculated / total * 100, 1) if total > 0 else 0.0
    return KpiCoverageStats(
        total_kpis=total,
        calculated=calculated,
        unavailable=unavailable,
        error=error,
        coverage_percent=coverage_pct,
    )


def _deduplicate_measurements(measurements: list[RawKpiResult]) -> list[RawKpiResult]:
    """
    If multiple evaluators produce the same KPI, prefer the 'calculated' one.
    Among multiple 'calculated', prefer the first one (kpi_calculator takes priority).
    """
    seen: dict[str, RawKpiResult] = {}
    for m in measurements:
        if m.kpi_name not in seen:
            seen[m.kpi_name] = m
        elif m.calculation_status == "calculated" and seen[m.kpi_name].calculation_status != "calculated":
            seen[m.kpi_name] = m
    return list(seen.values())


def calculate_kpis_for_run(run_id: int, db: Session) -> list[RawKpiResult]:
    """
    Calculate KPIs for an Evaluation Run and persist KpiMeasurement records.
    Returns the list of RawKpiResult objects.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise ValueError(f"Evaluation run {run_id} not found")

    traces = db.query(AgentTrace).filter(AgentTrace.evaluation_run_id == run_id).all()
    tool_traces = (
        db.query(ToolTrace)
        .join(AgentTrace, ToolTrace.agent_trace_id == AgentTrace.id)
        .filter(AgentTrace.evaluation_run_id == run_id)
        .all()
    )
    test_case_results = (
        db.query(TestCaseResult)
        .filter(TestCaseResult.evaluation_run_id == run_id)
        .all()
    )

    # 1. Core telemetry-derived KPIs
    measurements = calculate_kpis_from_run(
        run=run,
        traces=traces,
        tool_traces=tool_traces,
        test_case_results=test_case_results,
        input_cost_per_1k=run.llm_input_cost_per_1k,
        output_cost_per_1k=run.llm_output_cost_per_1k,
    )

    # 2. Run additional evaluators (accuracy, tool, safety, llm_judge)
    for evaluator in _EVALUATORS:
        try:
            eval_results = evaluator.evaluate(run, traces, tool_traces, test_case_results)
            measurements.extend(eval_results)
        except NotImplementedError:
            logger.info("Evaluator %s: not yet implemented, skipping.", evaluator.name)
        except Exception as exc:
            logger.error("Evaluator %s failed: %s", evaluator.name, exc)

    # 3. Deduplicate (prefer calculated over unavailable)
    measurements = _deduplicate_measurements(measurements)

    # 4. Persist to database (replace any existing measurements for this run)
    db.query(KpiMeasurement).filter(KpiMeasurement.evaluation_run_id == run_id).delete()
    for m in measurements:
        record = KpiMeasurement(
            evaluation_run_id=run_id,
            kpi_name=m.kpi_name,
            raw_value=m.raw_value,
            unit=m.unit,
            source=m.source,
            calculation_status=m.calculation_status,
            notes=m.notes,
        )
        db.add(record)
    db.commit()

    logger.info(
        "KPI calculation complete for run %d: %d/%d KPIs calculated.",
        run_id,
        sum(1 for m in measurements if m.calculation_status == "calculated"),
        len(measurements),
    )
    return measurements


def generate_evaluation_from_run(run_id: int, db: Session) -> Evaluation:
    """
    Full pipeline:
      1. Calculate KPIs (or use existing measurements)
      2. Map calculated KPI values → EvaluationCreate
      3. Call existing CARE scoring engine
      4. Call existing recommendation engine
      5. Save Evaluation record
      6. Link evaluation_id back to EvaluationRun

    This function does NOT modify or duplicate any scoring logic.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise ValueError(f"Evaluation run {run_id} not found")

    if run.status not in ("COMPLETED", "RUNNING"):
        raise ValueError(
            f"Evaluation run {run_id} is in status '{run.status}'. "
            "Only COMPLETED or RUNNING runs can generate evaluations."
        )

    # 1. Calculate KPIs (recalculate to ensure freshness)
    measurements = calculate_kpis_for_run(run_id, db)

    # 2. Build a lookup: kpi_name → raw_value (only for calculated KPIs)
    kpi_values: dict[str, Optional[float]] = {
        m.kpi_name: m.raw_value
        for m in measurements
        if m.calculation_status == "calculated"
    }

    # 3. Map to EvaluationCreate sub-objects
    #    IMPORTANT: unavailable KPIs → None (never zero)
    ci = ComputationalIntelligenceKPIs(
        relevance_score=kpi_values.get("relevance_score"),
        reasoning_quality=kpi_values.get("reasoning_quality"),
        completeness=kpi_values.get("completeness"),
        tool_selection_accuracy=kpi_values.get("tool_selection_accuracy"),
        planning_success_rate=kpi_values.get("planning_success_rate"),
        task_decomposition_accuracy=kpi_values.get("task_decomposition_accuracy"),
        recommendation_acceptance_rate=kpi_values.get("recommendation_acceptance_rate"),
    )
    acc = AccuracyKPIs(
        task_success_rate=kpi_values.get("task_success_rate"),
        precision=kpi_values.get("precision"),
        recall=kpi_values.get("recall"),
        hallucination_rate=kpi_values.get("hallucination_rate"),
        goal_completion_rate=kpi_values.get("goal_completion_rate"),
    )
    rel = ReliabilityKPIs(
        failure_rate=kpi_values.get("failure_rate"),
        retry_rate=kpi_values.get("retry_rate"),
        tool_success_rate=kpi_values.get("tool_success_rate"),
        latency_ms=kpi_values.get("latency_ms"),
        consistency_score=kpi_values.get("consistency_score"),
        error_recovery_rate=kpi_values.get("error_recovery_rate"),
        safety_violation_rate=kpi_values.get("safety_violation_rate"),
        policy_compliance_score=kpi_values.get("policy_compliance_score"),
        audit_coverage=kpi_values.get("audit_coverage"),
        pii_leakage_rate=kpi_values.get("pii_leakage_rate"),
    )
    eco = EconomicsKPIs(
        cost_per_task=kpi_values.get("cost_per_task"),
        token_consumption=kpi_values.get("token_consumption"),
        throughput=kpi_values.get("throughput"),
        resource_utilization=kpi_values.get("resource_utilization"),
        human_effort_saved=kpi_values.get("human_effort_saved"),
        productivity_improvement=kpi_values.get("productivity_improvement"),
        business_roi=kpi_values.get("business_roi"),
        payback_period_months=kpi_values.get("payback_period_months"),
        cost_per_successful_task=kpi_values.get("cost_per_successful_task"),
    )

    eval_create = EvaluationCreate(
        agent_name=run.agent_name,
        agent_type=run.agent_type,
        description=run.description or f"Automated evaluation run #{run_id}",
        evaluator="automated_pipeline",
        computational_intelligence=ci,
        accuracy=acc,
        reliability=rel,
        economics=eco,
    )

    # 4. Call the EXISTING scoring engine (no duplication)
    weights = _get_active_weights(db)
    scoring_result = run_scoring(eval_create, weights)

    # 5. Call the EXISTING recommendation engine (no duplication)
    strengths, weaknesses, recs = generate_recommendations(
        scoring_result["score_c"],
        scoring_result["score_a"],
        scoring_result["score_r"],
        scoring_result["score_e"],
        scoring_result["kpi_scores"],
    )

    # 6. Persist Evaluation record (same structure as manual evaluations)
    db_eval = Evaluation(
        agent_name=run.agent_name,
        agent_type=run.agent_type,
        description=eval_create.description,
        evaluator="automated_pipeline",
        weight_c=weights.weight_c,
        weight_a=weights.weight_a,
        weight_r=weights.weight_r,
        weight_e=weights.weight_e,
        score_c=scoring_result["score_c"],
        score_a=scoring_result["score_a"],
        score_r=scoring_result["score_r"],
        score_e=scoring_result["score_e"],
        care_score=scoring_result["care_score"],
        recommendation=scoring_result["recommendation"],
        kpi_scores=scoring_result["kpi_scores"],
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recs,
        # Raw KPI values from calculator
        relevance_score=kpi_values.get("relevance_score"),
        reasoning_quality=kpi_values.get("reasoning_quality"),
        completeness=kpi_values.get("completeness"),
        tool_selection_accuracy=kpi_values.get("tool_selection_accuracy"),
        planning_success_rate=kpi_values.get("planning_success_rate"),
        task_decomposition_accuracy=kpi_values.get("task_decomposition_accuracy"),
        recommendation_acceptance_rate=kpi_values.get("recommendation_acceptance_rate"),
        task_success_rate=kpi_values.get("task_success_rate"),
        precision=kpi_values.get("precision"),
        recall=kpi_values.get("recall"),
        hallucination_rate=kpi_values.get("hallucination_rate"),
        goal_completion_rate=kpi_values.get("goal_completion_rate"),
        failure_rate=kpi_values.get("failure_rate"),
        retry_rate=kpi_values.get("retry_rate"),
        tool_success_rate=kpi_values.get("tool_success_rate"),
        latency_ms=kpi_values.get("latency_ms"),
        consistency_score=kpi_values.get("consistency_score"),
        error_recovery_rate=kpi_values.get("error_recovery_rate"),
        safety_violation_rate=kpi_values.get("safety_violation_rate"),
        policy_compliance_score=kpi_values.get("policy_compliance_score"),
        audit_coverage=kpi_values.get("audit_coverage"),
        pii_leakage_rate=kpi_values.get("pii_leakage_rate"),
        cost_per_task=kpi_values.get("cost_per_task"),
        token_consumption=kpi_values.get("token_consumption"),
        throughput=kpi_values.get("throughput"),
        resource_utilization=kpi_values.get("resource_utilization"),
        human_effort_saved=kpi_values.get("human_effort_saved"),
        productivity_improvement=kpi_values.get("productivity_improvement"),
        business_roi=kpi_values.get("business_roi"),
        payback_period_months=kpi_values.get("payback_period_months"),
        cost_per_successful_task=kpi_values.get("cost_per_successful_task"),
    )
    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)

    # 7. Link evaluation_id back to the run
    run.evaluation_id = db_eval.id
    run.status = "COMPLETED"
    if run.completed_at is None:
        run.completed_at = datetime.utcnow()
    db.commit()

    logger.info(
        "Evaluation %d generated from run %d – CARE Score: %.1f – Recommendation: %s",
        db_eval.id, run_id, db_eval.care_score or 0, db_eval.recommendation,
    )
    return db_eval
