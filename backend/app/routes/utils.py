"""
Seed + Export Routes
====================
Database seeding and CSV export endpoints.
"""
import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.utils.seed_data import seed_database
from app.models.evaluation import Evaluation

router = APIRouter(prefix="/utils", tags=["Utilities"])


@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    """Seed the database with sample evaluations. Safe to call multiple times."""
    result = seed_database(db)
    return {"message": "Seed complete", "result": result}


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """Export all evaluations as a CSV file."""
    evaluations = db.query(Evaluation).order_by(Evaluation.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "id", "agent_name", "agent_type", "description", "evaluator",
        "care_score", "score_c", "score_a", "score_r", "score_e",
        "recommendation", "created_at",
        "weight_c", "weight_a", "weight_r", "weight_e",
        # C KPIs
        "relevance_score", "reasoning_quality", "completeness",
        "tool_selection_accuracy", "planning_success_rate",
        "task_decomposition_accuracy", "recommendation_acceptance_rate",
        # A KPIs
        "task_success_rate", "precision", "recall",
        "hallucination_rate", "goal_completion_rate",
        # R KPIs
        "failure_rate", "retry_rate", "tool_success_rate", "latency_ms",
        "consistency_score", "error_recovery_rate", "safety_violation_rate",
        "policy_compliance_score", "audit_coverage", "pii_leakage_rate",
        # E KPIs
        "cost_per_task", "token_consumption", "throughput",
        "resource_utilization", "human_effort_saved", "productivity_improvement",
        "business_roi", "payback_period_months", "cost_per_successful_task",
    ]
    writer.writerow(headers)

    for ev in evaluations:
        writer.writerow([getattr(ev, h, "") for h in headers])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=care_evaluations.csv"},
    )
