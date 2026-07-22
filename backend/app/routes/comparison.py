"""
Comparison API Routes
=====================
Compare multiple AI agents side by side.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.evaluation import Evaluation
from app.schemas.evaluation import ComparisonRequest, ComparisonResult, EvaluationSummary, DimensionComparison

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.post("/", response_model=ComparisonResult)
def compare_evaluations(request: ComparisonRequest, db: Session = Depends(get_db)):
    """Compare multiple evaluations and return side-by-side analysis."""
    evaluations = db.query(Evaluation).filter(
        Evaluation.id.in_(request.evaluation_ids)
    ).all()

    if len(evaluations) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"At least 2 valid evaluations required. Found {len(evaluations)}."
        )

    # Build summaries
    summaries = [
        EvaluationSummary(
            id=ev.id, agent_name=ev.agent_name, agent_type=ev.agent_type,
            care_score=ev.care_score, score_c=ev.score_c, score_a=ev.score_a,
            score_r=ev.score_r, score_e=ev.score_e,
            recommendation=ev.recommendation, created_at=ev.created_at,
        )
        for ev in evaluations
    ]

    # CARE score comparison dict
    care_scores = {ev.agent_name: (ev.care_score or 0) for ev in evaluations}

    # Per-dimension comparisons
    dimension_comps: List[DimensionComparison] = []
    dims = [
        ("Computational Intelligence", "score_c"),
        ("Accuracy", "score_a"),
        ("Reliability", "score_r"),
        ("Economics", "score_e"),
    ]
    for dim_name, attr in dims:
        scores = {ev.agent_name: (getattr(ev, attr) or 0) for ev in evaluations}
        winner = max(scores, key=lambda k: scores[k])
        dimension_comps.append(DimensionComparison(
            dimension=dim_name, scores=scores, winner=winner
        ))

    # Overall winner
    overall_winner = max(care_scores, key=lambda k: care_scores[k])

    # KPI comparison table
    kpi_fields = [
        "relevance_score", "reasoning_quality", "completeness",
        "tool_selection_accuracy", "planning_success_rate",
        "task_decomposition_accuracy", "recommendation_acceptance_rate",
        "task_success_rate", "precision", "recall",
        "hallucination_rate", "goal_completion_rate",
        "failure_rate", "retry_rate", "tool_success_rate", "latency_ms",
        "consistency_score", "error_recovery_rate", "safety_violation_rate",
        "policy_compliance_score", "audit_coverage", "pii_leakage_rate",
        "cost_per_task", "token_consumption", "throughput",
        "resource_utilization", "human_effort_saved", "productivity_improvement",
        "business_roi", "payback_period_months", "cost_per_successful_task",
    ]
    kpi_comparison = {}
    for kpi in kpi_fields:
        row = {}
        for ev in evaluations:
            row[ev.agent_name] = getattr(ev, kpi, None)
        kpi_comparison[kpi] = row

    return ComparisonResult(
        agents=summaries,
        dimension_comparisons=dimension_comps,
        care_score_comparison=care_scores,
        overall_winner=overall_winner,
        kpi_comparison=kpi_comparison,
    )
