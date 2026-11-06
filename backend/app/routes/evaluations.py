"""
Evaluations API Routes
======================
Full CRUD for evaluations plus bulk operations (compare, duplicate).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.database import get_db
from app.models.evaluation import Evaluation, WeightConfig
from app.schemas.evaluation import (
    EvaluationCreate, EvaluationRead, EvaluationUpdate, EvaluationSummary,
    WeightConfigBase,
)
from app.services.scoring import run_scoring
from app.services.recommendations import generate_recommendations
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    tracer = trace.get_tracer(__name__)
except ImportError:
    import contextlib
    class DummySpan:
        def set_attribute(self, *a, **kw): pass
        def set_status(self, *a, **kw): pass
        def record_exception(self, *a, **kw): pass
        def add_event(self, *a, **kw): pass
    class DummyTracer:
        @contextlib.contextmanager
        def start_as_current_span(self, name, *args, **kwargs):
            yield DummySpan()
    tracer = DummyTracer()
    class Status:
        def __init__(self, *a, **kw): pass
    class StatusCode:
        ERROR = "ERROR"
        OK = "OK"

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])



def _get_active_weights(db: Session) -> WeightConfigBase:
    """Fetch the active weight config from DB (creates default if missing)."""
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


def _build_evaluation_from_create(data: EvaluationCreate, weights: WeightConfigBase) -> dict:
    """Run scoring pipeline and return a dict of all fields for the ORM model."""
    result = run_scoring(data, weights)
    strengths, weaknesses, recs = generate_recommendations(
        result["score_c"], result["score_a"],
        result["score_r"], result["score_e"],
        result["kpi_scores"],
    )
    ci = data.computational_intelligence
    acc = data.accuracy
    rel = data.reliability
    eco = data.economics
    return {
        "agent_name": data.agent_name,
        "agent_type": data.agent_type,
        "description": data.description,
        "evaluator": data.evaluator,
        "weight_c": weights.weight_c, "weight_a": weights.weight_a,
        "weight_r": weights.weight_r, "weight_e": weights.weight_e,
        "score_c": result["score_c"], "score_a": result["score_a"],
        "score_r": result["score_r"], "score_e": result["score_e"],
        "care_score": result["care_score"],
        "recommendation": result["recommendation"],
        "kpi_scores": result["kpi_scores"],
        "strengths": strengths, "weaknesses": weaknesses, "recommendations": recs,
        # C KPIs
        "relevance_score": ci.relevance_score, "reasoning_quality": ci.reasoning_quality,
        "completeness": ci.completeness, "tool_selection_accuracy": ci.tool_selection_accuracy,
        "planning_success_rate": ci.planning_success_rate,
        "task_decomposition_accuracy": ci.task_decomposition_accuracy,
        "recommendation_acceptance_rate": ci.recommendation_acceptance_rate,
        # A KPIs
        "task_success_rate": acc.task_success_rate, "precision": acc.precision,
        "recall": acc.recall, "hallucination_rate": acc.hallucination_rate,
        "goal_completion_rate": acc.goal_completion_rate,
        # R KPIs
        "failure_rate": rel.failure_rate, "retry_rate": rel.retry_rate,
        "tool_success_rate": rel.tool_success_rate, "latency_ms": rel.latency_ms,
        "consistency_score": rel.consistency_score, "error_recovery_rate": rel.error_recovery_rate,
        "safety_violation_rate": rel.safety_violation_rate,
        "policy_compliance_score": rel.policy_compliance_score,
        "audit_coverage": rel.audit_coverage, "pii_leakage_rate": rel.pii_leakage_rate,
        # E KPIs
        "cost_per_task": eco.cost_per_task, "token_consumption": eco.token_consumption,
        "throughput": eco.throughput, "resource_utilization": eco.resource_utilization,
        "human_effort_saved": eco.human_effort_saved,
        "productivity_improvement": eco.productivity_improvement,
        "business_roi": eco.business_roi, "payback_period_months": eco.payback_period_months,
        "cost_per_successful_task": eco.cost_per_successful_task,
    }


@router.post("/", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(data: EvaluationCreate, db: Session = Depends(get_db)):

    with tracer.start_as_current_span("create_evaluation") as span:

        span.set_attribute("agent.name", data.agent_name)
        span.set_attribute("agent.type", data.agent_type)

        weights = _get_active_weights(db)

        fields = _build_evaluation_from_create(data, weights)

        db_eval = Evaluation(**fields)

        with tracer.start_as_current_span("save_database") as db_span:
         try:
             db_span.add_event("Saving evaluation to database")

             db.add(db_eval)
             db.commit()
             db.refresh(db_eval)

             db_span.set_attribute("database.operation", "INSERT")
             db_span.set_attribute("database.table", "evaluations")
             db_span.set_attribute("evaluation.id", db_eval.id)
             db_span.set_attribute("agent.name", db_eval.agent_name)
             db_span.set_attribute("care.score", db_eval.care_score)

             db_span.add_event("Database save successful")

         except Exception as e:
             db.rollback()
             db_span.record_exception(e)
             db_span.set_status(Status(StatusCode.ERROR))
             raise

        span.set_attribute("care.score", db_eval.care_score)
        span.set_attribute("recommendation", db_eval.recommendation)

        return db_eval


@router.get("/", response_model=List[EvaluationSummary])
def list_evaluations(
    search: Optional[str] = Query(None, description="Search by agent name or type"),
    agent_type: Optional[str] = Query(None),
    recommendation: Optional[str] = Query(None),
    sort_by: str = Query("created_at", enum=["created_at", "care_score", "agent_name"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List evaluations with search, filter, sort, and pagination."""
    query = db.query(Evaluation)

    if search:
        query = query.filter(
            or_(
                Evaluation.agent_name.ilike(f"%{search}%"),
                Evaluation.agent_type.ilike(f"%{search}%"),
            )
        )
    if agent_type:
        query = query.filter(Evaluation.agent_type.ilike(f"%{agent_type}%"))
    if recommendation:
        query = query.filter(Evaluation.recommendation == recommendation)

    sort_col = getattr(Evaluation, sort_by, Evaluation.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    return query.offset(skip).limit(limit).all()


@router.get("/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get a single evaluation by ID."""
    ev = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return ev


@router.put("/{evaluation_id}", response_model=EvaluationRead)
def update_evaluation(
    evaluation_id: int, data: EvaluationUpdate, db: Session = Depends(get_db)
):
    """Update an evaluation and recompute scores."""
    ev = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Merge existing KPIs with the update payload
    if data.agent_name:
        ev.agent_name = data.agent_name
    if data.agent_type:
        ev.agent_type = data.agent_type
    if data.description is not None:
        ev.description = data.description

    if data.computational_intelligence or data.accuracy or data.reliability or data.economics:
        # Reconstruct a full EvaluationCreate from existing + updated values
        from app.schemas.evaluation import (
            ComputationalIntelligenceKPIs, AccuracyKPIs, ReliabilityKPIs, EconomicsKPIs
        )
        ci_update = data.computational_intelligence or ComputationalIntelligenceKPIs()
        acc_update = data.accuracy or AccuracyKPIs()
        rel_update = data.reliability or ReliabilityKPIs()
        eco_update = data.economics or EconomicsKPIs()

        full_create = EvaluationCreate(
            agent_name=ev.agent_name, agent_type=ev.agent_type,
            description=ev.description, evaluator=ev.evaluator,
            computational_intelligence=ComputationalIntelligenceKPIs(
                relevance_score=ci_update.relevance_score or ev.relevance_score,
                reasoning_quality=ci_update.reasoning_quality or ev.reasoning_quality,
                completeness=ci_update.completeness or ev.completeness,
                tool_selection_accuracy=ci_update.tool_selection_accuracy or ev.tool_selection_accuracy,
                planning_success_rate=ci_update.planning_success_rate or ev.planning_success_rate,
                task_decomposition_accuracy=ci_update.task_decomposition_accuracy or ev.task_decomposition_accuracy,
                recommendation_acceptance_rate=ci_update.recommendation_acceptance_rate or ev.recommendation_acceptance_rate,
            ),
            accuracy=AccuracyKPIs(
                task_success_rate=acc_update.task_success_rate or ev.task_success_rate,
                precision=acc_update.precision or ev.precision,
                recall=acc_update.recall or ev.recall,
                hallucination_rate=acc_update.hallucination_rate if acc_update.hallucination_rate is not None else ev.hallucination_rate,
                goal_completion_rate=acc_update.goal_completion_rate or ev.goal_completion_rate,
            ),
            reliability=ReliabilityKPIs(
                failure_rate=rel_update.failure_rate if rel_update.failure_rate is not None else ev.failure_rate,
                retry_rate=rel_update.retry_rate if rel_update.retry_rate is not None else ev.retry_rate,
                tool_success_rate=rel_update.tool_success_rate or ev.tool_success_rate,
                latency_ms=rel_update.latency_ms or ev.latency_ms,
                consistency_score=rel_update.consistency_score or ev.consistency_score,
                error_recovery_rate=rel_update.error_recovery_rate or ev.error_recovery_rate,
                safety_violation_rate=rel_update.safety_violation_rate if rel_update.safety_violation_rate is not None else ev.safety_violation_rate,
                policy_compliance_score=rel_update.policy_compliance_score or ev.policy_compliance_score,
                audit_coverage=rel_update.audit_coverage or ev.audit_coverage,
                pii_leakage_rate=rel_update.pii_leakage_rate if rel_update.pii_leakage_rate is not None else ev.pii_leakage_rate,
            ),
            economics=EconomicsKPIs(
                cost_per_task=eco_update.cost_per_task or ev.cost_per_task,
                token_consumption=eco_update.token_consumption or ev.token_consumption,
                throughput=eco_update.throughput or ev.throughput,
                resource_utilization=eco_update.resource_utilization or ev.resource_utilization,
                human_effort_saved=eco_update.human_effort_saved or ev.human_effort_saved,
                productivity_improvement=eco_update.productivity_improvement or ev.productivity_improvement,
                business_roi=eco_update.business_roi if eco_update.business_roi is not None else ev.business_roi,
                payback_period_months=eco_update.payback_period_months or ev.payback_period_months,
                cost_per_successful_task=eco_update.cost_per_successful_task or ev.cost_per_successful_task,
            ),
        )
        weights = WeightConfigBase(
            weight_c=ev.weight_c, weight_a=ev.weight_a,
            weight_r=ev.weight_r, weight_e=ev.weight_e,
        )
        fields = _build_evaluation_from_create(full_create, weights)
        for key, val in fields.items():
            if key not in ("agent_name", "agent_type", "description"):
                setattr(ev, key, val)

    db.commit()
    db.refresh(ev)
    return ev


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Delete an evaluation by ID."""
    ev = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    db.delete(ev)
    db.commit()


@router.post("/{evaluation_id}/duplicate", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def duplicate_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Duplicate an existing evaluation."""
    ev = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    from sqlalchemy.orm import make_transient
    db.expunge(ev)
    make_transient(ev)
    ev.id = None
    ev.agent_name = f"{ev.agent_name} (Copy)"
    from datetime import datetime
    ev.created_at = datetime.utcnow()
    ev.updated_at = datetime.utcnow()
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev
