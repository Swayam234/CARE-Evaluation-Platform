"""
Seed Data Utility
=================
Seeds the database with 4 representative sample evaluations for demonstration.
Safe to call multiple times (checks for existing data first).
"""
from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation, WeightConfig
from app.schemas.evaluation import EvaluationCreate, WeightConfigBase
from app.schemas.evaluation import (
    ComputationalIntelligenceKPIs, AccuracyKPIs, ReliabilityKPIs, EconomicsKPIs
)
from app.services.scoring import run_scoring
from app.services.recommendations import generate_recommendations


SAMPLE_EVALUATIONS = [
    {
        "agent_name": "Resume Screening Agent",
        "agent_type": "Document Processing Agent",
        "description": "Automated resume screening agent for HR talent acquisition. Parses resumes, scores candidates against job descriptions, and shortlists top applicants.",
        "evaluator": "HR Technology Team",
        "computational_intelligence": ComputationalIntelligenceKPIs(
            relevance_score=82.0, reasoning_quality=78.0, completeness=85.0,
            tool_selection_accuracy=88.0, planning_success_rate=80.0,
            task_decomposition_accuracy=76.0, recommendation_acceptance_rate=72.0,
        ),
        "accuracy": AccuracyKPIs(
            task_success_rate=91.0, precision=88.0, recall=84.0,
            hallucination_rate=8.0, goal_completion_rate=89.0,
        ),
        "reliability": ReliabilityKPIs(
            failure_rate=4.0, retry_rate=6.0, tool_success_rate=94.0,
            latency_ms=1200.0, consistency_score=86.0, error_recovery_rate=78.0,
            safety_violation_rate=2.0, policy_compliance_score=92.0,
            audit_coverage=88.0, pii_leakage_rate=1.5,
        ),
        "economics": EconomicsKPIs(
            cost_per_task=0.05, token_consumption=2500.0, throughput=120.0,
            resource_utilization=72.0, human_effort_saved=78.0,
            productivity_improvement=65.0, business_roi=320.0,
            payback_period_months=4.0, cost_per_successful_task=0.06,
        ),
    },
    {
        "agent_name": "Sales Assistant Agent",
        "agent_type": "Conversational Sales Agent",
        "description": "AI-powered sales assistant that qualifies leads, answers product questions, schedules demos, and assists with proposal generation.",
        "evaluator": "Sales Operations Team",
        "computational_intelligence": ComputationalIntelligenceKPIs(
            relevance_score=90.0, reasoning_quality=87.0, completeness=83.0,
            tool_selection_accuracy=85.0, planning_success_rate=88.0,
            task_decomposition_accuracy=82.0, recommendation_acceptance_rate=79.0,
        ),
        "accuracy": AccuracyKPIs(
            task_success_rate=85.0, precision=82.0, recall=79.0,
            hallucination_rate=12.0, goal_completion_rate=84.0,
        ),
        "reliability": ReliabilityKPIs(
            failure_rate=8.0, retry_rate=10.0, tool_success_rate=88.0,
            latency_ms=800.0, consistency_score=80.0, error_recovery_rate=72.0,
            safety_violation_rate=3.0, policy_compliance_score=87.0,
            audit_coverage=82.0, pii_leakage_rate=2.0,
        ),
        "economics": EconomicsKPIs(
            cost_per_task=0.12, token_consumption=5000.0, throughput=80.0,
            resource_utilization=68.0, human_effort_saved=60.0,
            productivity_improvement=45.0, business_roi=220.0,
            payback_period_months=6.0, cost_per_successful_task=0.14,
        ),
    },
    {
        "agent_name": "HR Performance Agent",
        "agent_type": "Analytics & Reporting Agent",
        "description": "Agent that analyses employee performance data, generates performance reviews, identifies high-potential employees, and recommends development plans.",
        "evaluator": "People Analytics Team",
        "computational_intelligence": ComputationalIntelligenceKPIs(
            relevance_score=75.0, reasoning_quality=70.0, completeness=72.0,
            tool_selection_accuracy=68.0, planning_success_rate=65.0,
            task_decomposition_accuracy=62.0, recommendation_acceptance_rate=58.0,
        ),
        "accuracy": AccuracyKPIs(
            task_success_rate=74.0, precision=70.0, recall=68.0,
            hallucination_rate=22.0, goal_completion_rate=71.0,
        ),
        "reliability": ReliabilityKPIs(
            failure_rate=15.0, retry_rate=18.0, tool_success_rate=78.0,
            latency_ms=3500.0, consistency_score=68.0, error_recovery_rate=60.0,
            safety_violation_rate=5.0, policy_compliance_score=75.0,
            audit_coverage=70.0, pii_leakage_rate=4.0,
        ),
        "economics": EconomicsKPIs(
            cost_per_task=0.25, token_consumption=8000.0, throughput=40.0,
            resource_utilization=55.0, human_effort_saved=42.0,
            productivity_improvement=30.0, business_roi=140.0,
            payback_period_months=10.0, cost_per_successful_task=0.34,
        ),
    },
    {
        "agent_name": "Customer Support Agent",
        "agent_type": "Customer Service Chatbot",
        "description": "Tier-1 customer support agent handling product inquiries, troubleshooting, returns, and escalations. Integrated with CRM and knowledge base.",
        "evaluator": "Customer Experience Team",
        "computational_intelligence": ComputationalIntelligenceKPIs(
            relevance_score=93.0, reasoning_quality=91.0, completeness=89.0,
            tool_selection_accuracy=94.0, planning_success_rate=92.0,
            task_decomposition_accuracy=88.0, recommendation_acceptance_rate=86.0,
        ),
        "accuracy": AccuracyKPIs(
            task_success_rate=95.0, precision=93.0, recall=91.0,
            hallucination_rate=4.0, goal_completion_rate=94.0,
        ),
        "reliability": ReliabilityKPIs(
            failure_rate=2.0, retry_rate=3.0, tool_success_rate=97.0,
            latency_ms=450.0, consistency_score=94.0, error_recovery_rate=92.0,
            safety_violation_rate=0.5, policy_compliance_score=98.0,
            audit_coverage=96.0, pii_leakage_rate=0.2,
        ),
        "economics": EconomicsKPIs(
            cost_per_task=0.008, token_consumption=1200.0, throughput=400.0,
            resource_utilization=85.0, human_effort_saved=88.0,
            productivity_improvement=150.0, business_roi=480.0,
            payback_period_months=2.0, cost_per_successful_task=0.009,
        ),
    },
]


def seed_database(db: Session) -> dict:
    """
    Seed the database with sample evaluations and default weight config.
    Returns a summary of what was seeded.
    """
    seeded = {"weight_config": False, "evaluations": []}

    # ── Ensure default weight config exists ──────────────────────────────────
    existing_config = db.query(WeightConfig).filter(WeightConfig.id == 1).first()
    if not existing_config:
        default_weights = WeightConfig(
            id=1, weight_c=0.25, weight_a=0.30, weight_r=0.30, weight_e=0.15
        )
        db.add(default_weights)
        db.commit()
        seeded["weight_config"] = True

    weights = WeightConfigBase(weight_c=0.25, weight_a=0.30, weight_r=0.30, weight_e=0.15)

    # ── Seed evaluations (skip if agent already exists) ───────────────────────
    for sample in SAMPLE_EVALUATIONS:
        existing = db.query(Evaluation).filter(
            Evaluation.agent_name == sample["agent_name"]
        ).first()
        if existing:
            seeded["evaluations"].append({"name": sample["agent_name"], "status": "already_exists"})
            continue

        eval_create = EvaluationCreate(
            agent_name=sample["agent_name"],
            agent_type=sample["agent_type"],
            description=sample["description"],
            evaluator=sample["evaluator"],
            computational_intelligence=sample["computational_intelligence"],
            accuracy=sample["accuracy"],
            reliability=sample["reliability"],
            economics=sample["economics"],
        )

        result = run_scoring(eval_create, weights)
        strengths, weaknesses, recs = generate_recommendations(
            result["score_c"], result["score_a"],
            result["score_r"], result["score_e"],
            result["kpi_scores"],
        )

        ci = eval_create.computational_intelligence
        acc = eval_create.accuracy
        rel = eval_create.reliability
        eco = eval_create.economics

        db_eval = Evaluation(
            agent_name=eval_create.agent_name,
            agent_type=eval_create.agent_type,
            description=eval_create.description,
            evaluator=eval_create.evaluator,
            weight_c=weights.weight_c, weight_a=weights.weight_a,
            weight_r=weights.weight_r, weight_e=weights.weight_e,
            score_c=result["score_c"], score_a=result["score_a"],
            score_r=result["score_r"], score_e=result["score_e"],
            care_score=result["care_score"],
            recommendation=result["recommendation"],
            kpi_scores=result["kpi_scores"],
            strengths=strengths, weaknesses=weaknesses,
            recommendations=recs,
            # CI KPIs
            relevance_score=ci.relevance_score, reasoning_quality=ci.reasoning_quality,
            completeness=ci.completeness, tool_selection_accuracy=ci.tool_selection_accuracy,
            planning_success_rate=ci.planning_success_rate,
            task_decomposition_accuracy=ci.task_decomposition_accuracy,
            recommendation_acceptance_rate=ci.recommendation_acceptance_rate,
            # Accuracy KPIs
            task_success_rate=acc.task_success_rate, precision=acc.precision,
            recall=acc.recall, hallucination_rate=acc.hallucination_rate,
            goal_completion_rate=acc.goal_completion_rate,
            # Reliability KPIs
            failure_rate=rel.failure_rate, retry_rate=rel.retry_rate,
            tool_success_rate=rel.tool_success_rate, latency_ms=rel.latency_ms,
            consistency_score=rel.consistency_score, error_recovery_rate=rel.error_recovery_rate,
            safety_violation_rate=rel.safety_violation_rate,
            policy_compliance_score=rel.policy_compliance_score,
            audit_coverage=rel.audit_coverage, pii_leakage_rate=rel.pii_leakage_rate,
            # Economics KPIs
            cost_per_task=eco.cost_per_task, token_consumption=eco.token_consumption,
            throughput=eco.throughput, resource_utilization=eco.resource_utilization,
            human_effort_saved=eco.human_effort_saved,
            productivity_improvement=eco.productivity_improvement,
            business_roi=eco.business_roi, payback_period_months=eco.payback_period_months,
            cost_per_successful_task=eco.cost_per_successful_task,
        )
        db.add(db_eval)
        db.commit()
        db.refresh(db_eval)
        seeded["evaluations"].append({
            "name": db_eval.agent_name,
            "status": "seeded",
            "care_score": db_eval.care_score,
        })

    return seeded
