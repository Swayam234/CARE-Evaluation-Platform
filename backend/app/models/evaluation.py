"""
SQLAlchemy ORM Models for the CARE Evaluation Platform.
Every evaluation stores raw KPI values, computed dimension scores,
the overall CARE score, and the weights used at evaluation time.
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON
from app.database.database import Base


class WeightConfig(Base):
    """
    Stores the active dimension weight configuration.
    Only one active row should exist at a time (id=1).
    """
    __tablename__ = "weight_configs"

    id = Column(Integer, primary_key=True, index=True)
    weight_c = Column(Float, default=0.25, nullable=False)  # Computational Intelligence
    weight_a = Column(Float, default=0.30, nullable=False)  # Accuracy
    weight_r = Column(Float, default=0.30, nullable=False)  # Reliability
    weight_e = Column(Float, default=0.15, nullable=False)  # Economics
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Evaluation(Base):
    """
    Core evaluation record.
    Stores all KPI inputs, computed scores, and metadata.
    """
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False)  # e.g. chatbot, RAG, coding, workflow
    description = Column(Text, nullable=True)
    evaluator = Column(String(255), nullable=True)   # Auth scaffold – future: FK to users
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Weights used at evaluation time (snapshot for historical accuracy) ──
    weight_c = Column(Float, default=0.25)
    weight_a = Column(Float, default=0.30)
    weight_r = Column(Float, default=0.30)
    weight_e = Column(Float, default=0.15)

    # ── Dimension Scores (0-100) ─────────────────────────────────────────────
    score_c = Column(Float, nullable=True)   # Computational Intelligence
    score_a = Column(Float, nullable=True)   # Accuracy
    score_r = Column(Float, nullable=True)   # Reliability
    score_e = Column(Float, nullable=True)   # Economics
    care_score = Column(Float, nullable=True)  # Overall CARE score
    recommendation = Column(String(100), nullable=True)  # Deployment recommendation

    # ── C: Computational Intelligence KPIs ──────────────────────────────────
    relevance_score = Column(Float, nullable=True)          # 0-100
    reasoning_quality = Column(Float, nullable=True)        # 0-100
    completeness = Column(Float, nullable=True)             # 0-100
    tool_selection_accuracy = Column(Float, nullable=True)  # 0-100
    planning_success_rate = Column(Float, nullable=True)    # 0-100
    task_decomposition_accuracy = Column(Float, nullable=True)  # 0-100
    recommendation_acceptance_rate = Column(Float, nullable=True)  # 0-100

    # ── A: Accuracy KPIs ────────────────────────────────────────────────────
    task_success_rate = Column(Float, nullable=True)        # 0-100
    precision = Column(Float, nullable=True)                # 0-100
    recall = Column(Float, nullable=True)                   # 0-100
    hallucination_rate = Column(Float, nullable=True)       # 0-100 (lower is better)
    goal_completion_rate = Column(Float, nullable=True)     # 0-100

    # ── R: Reliability KPIs ─────────────────────────────────────────────────
    failure_rate = Column(Float, nullable=True)             # 0-100 (lower is better)
    retry_rate = Column(Float, nullable=True)               # 0-100 (lower is better)
    tool_success_rate = Column(Float, nullable=True)        # 0-100
    latency_ms = Column(Float, nullable=True)               # raw ms (normalized internally)
    consistency_score = Column(Float, nullable=True)        # 0-100
    error_recovery_rate = Column(Float, nullable=True)      # 0-100
    safety_violation_rate = Column(Float, nullable=True)    # 0-100 (lower is better)
    policy_compliance_score = Column(Float, nullable=True)  # 0-100
    audit_coverage = Column(Float, nullable=True)           # 0-100
    pii_leakage_rate = Column(Float, nullable=True)         # 0-100 (lower is better)

    # ── E: Economics KPIs ───────────────────────────────────────────────────
    cost_per_task = Column(Float, nullable=True)            # raw $ (normalized internally)
    token_consumption = Column(Float, nullable=True)        # raw tokens (normalized)
    throughput = Column(Float, nullable=True)               # tasks/hour (higher is better)
    resource_utilization = Column(Float, nullable=True)     # 0-100
    human_effort_saved = Column(Float, nullable=True)       # 0-100
    productivity_improvement = Column(Float, nullable=True) # percentage (normalized)
    business_roi = Column(Float, nullable=True)             # percentage (normalized)
    payback_period_months = Column(Float, nullable=True)    # months (lower is better)
    cost_per_successful_task = Column(Float, nullable=True) # raw $ (normalized)

    # ── Computed details (JSON) ──────────────────────────────────────────────
    strengths = Column(JSON, nullable=True)       # list of strength strings
    weaknesses = Column(JSON, nullable=True)      # list of weakness strings
    recommendations = Column(JSON, nullable=True) # list of recommendation dicts
    kpi_scores = Column(JSON, nullable=True)      # normalized per-KPI scores map
