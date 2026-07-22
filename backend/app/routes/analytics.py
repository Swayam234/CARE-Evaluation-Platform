"""
Analytics API Routes
====================
Aggregated analytics, trends, and summary statistics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.evaluation import Evaluation
from app.schemas.evaluation import AnalyticsSummary, TrendPoint, EvaluationSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Return aggregated analytics for all evaluations."""
    all_evals = db.query(Evaluation).order_by(Evaluation.created_at.asc()).all()
    total = len(all_evals)

    if total == 0:
        return AnalyticsSummary(
            total_evaluations=0, avg_care_score=0,
            avg_score_c=0, avg_score_a=0, avg_score_r=0, avg_score_e=0,
            production_ready_count=0, not_recommended_count=0,
            trend=[], score_distribution={}, top_agents=[],
        )

    def _safe_avg(vals):
        clean = [v for v in vals if v is not None]
        return round(sum(clean) / len(clean), 2) if clean else 0.0

    avg_care = _safe_avg([e.care_score for e in all_evals])
    avg_c = _safe_avg([e.score_c for e in all_evals])
    avg_a = _safe_avg([e.score_a for e in all_evals])
    avg_r = _safe_avg([e.score_r for e in all_evals])
    avg_e = _safe_avg([e.score_e for e in all_evals])

    production_ready = sum(1 for e in all_evals if e.recommendation == "Production Ready")
    not_recommended = sum(1 for e in all_evals if e.recommendation == "Not Recommended")

    # Trend points (one per evaluation ordered by date)
    trend = []
    for ev in all_evals:
        if ev.care_score is not None:
            trend.append(TrendPoint(
                date=ev.created_at.strftime("%Y-%m-%d"),
                care_score=ev.care_score or 0,
                score_c=ev.score_c or 0,
                score_a=ev.score_a or 0,
                score_r=ev.score_r or 0,
                score_e=ev.score_e or 0,
                agent_name=ev.agent_name,
            ))

    # Score distribution buckets
    distribution = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for ev in all_evals:
        s = ev.care_score or 0
        if s >= 90:
            distribution["90-100"] += 1
        elif s >= 80:
            distribution["80-89"] += 1
        elif s >= 70:
            distribution["70-79"] += 1
        elif s >= 60:
            distribution["60-69"] += 1
        else:
            distribution["0-59"] += 1

    # Top 5 agents by CARE score
    top = sorted([e for e in all_evals if e.care_score is not None],
                 key=lambda e: e.care_score, reverse=True)[:5]
    top_agents = [
        EvaluationSummary(
            id=e.id, agent_name=e.agent_name, agent_type=e.agent_type,
            care_score=e.care_score, score_c=e.score_c, score_a=e.score_a,
            score_r=e.score_r, score_e=e.score_e,
            recommendation=e.recommendation, created_at=e.created_at,
        ) for e in top
    ]

    return AnalyticsSummary(
        total_evaluations=total,
        avg_care_score=avg_care,
        avg_score_c=avg_c,
        avg_score_a=avg_a,
        avg_score_r=avg_r,
        avg_score_e=avg_e,
        production_ready_count=production_ready,
        not_recommended_count=not_recommended,
        trend=trend,
        score_distribution=distribution,
        top_agents=top_agents,
    )
