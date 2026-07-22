"""
Pydantic schemas for the CARE Evaluation Platform.
Separate schemas for create/read/update to follow clean architecture.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ─── Weight Config ────────────────────────────────────────────────────────────

class WeightConfigBase(BaseModel):
    weight_c: float = Field(0.25, ge=0.0, le=1.0, description="Computational Intelligence weight")
    weight_a: float = Field(0.30, ge=0.0, le=1.0, description="Accuracy weight")
    weight_r: float = Field(0.30, ge=0.0, le=1.0, description="Reliability weight")
    weight_e: float = Field(0.15, ge=0.0, le=1.0, description="Economics weight")

    @validator("weight_e", always=True)
    def weights_must_sum_to_one(cls, v, values):
        total = values.get("weight_c", 0) + values.get("weight_a", 0) + values.get("weight_r", 0) + v
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")
        return v


class WeightConfigRead(WeightConfigBase):
    id: int
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Evaluation KPI Input ─────────────────────────────────────────────────────

class ComputationalIntelligenceKPIs(BaseModel):
    relevance_score: Optional[float] = Field(None, ge=0, le=100)
    reasoning_quality: Optional[float] = Field(None, ge=0, le=100)
    completeness: Optional[float] = Field(None, ge=0, le=100)
    tool_selection_accuracy: Optional[float] = Field(None, ge=0, le=100)
    planning_success_rate: Optional[float] = Field(None, ge=0, le=100)
    task_decomposition_accuracy: Optional[float] = Field(None, ge=0, le=100)
    recommendation_acceptance_rate: Optional[float] = Field(None, ge=0, le=100)


class AccuracyKPIs(BaseModel):
    task_success_rate: Optional[float] = Field(None, ge=0, le=100)
    precision: Optional[float] = Field(None, ge=0, le=100)
    recall: Optional[float] = Field(None, ge=0, le=100)
    hallucination_rate: Optional[float] = Field(None, ge=0, le=100)   # lower is better
    goal_completion_rate: Optional[float] = Field(None, ge=0, le=100)


class ReliabilityKPIs(BaseModel):
    failure_rate: Optional[float] = Field(None, ge=0, le=100)          # lower is better
    retry_rate: Optional[float] = Field(None, ge=0, le=100)            # lower is better
    tool_success_rate: Optional[float] = Field(None, ge=0, le=100)
    latency_ms: Optional[float] = Field(None, ge=0)                    # raw ms
    consistency_score: Optional[float] = Field(None, ge=0, le=100)
    error_recovery_rate: Optional[float] = Field(None, ge=0, le=100)
    safety_violation_rate: Optional[float] = Field(None, ge=0, le=100) # lower is better
    policy_compliance_score: Optional[float] = Field(None, ge=0, le=100)
    audit_coverage: Optional[float] = Field(None, ge=0, le=100)
    pii_leakage_rate: Optional[float] = Field(None, ge=0, le=100)      # lower is better


class EconomicsKPIs(BaseModel):
    cost_per_task: Optional[float] = Field(None, ge=0)                 # raw $
    token_consumption: Optional[float] = Field(None, ge=0)             # raw tokens
    throughput: Optional[float] = Field(None, ge=0)                    # tasks/hour
    resource_utilization: Optional[float] = Field(None, ge=0, le=100)
    human_effort_saved: Optional[float] = Field(None, ge=0, le=100)
    productivity_improvement: Optional[float] = Field(None, ge=0)      # percentage
    business_roi: Optional[float] = Field(None)                        # percentage (can be negative)
    payback_period_months: Optional[float] = Field(None, ge=0)         # months
    cost_per_successful_task: Optional[float] = Field(None, ge=0)      # raw $


# ─── Evaluation Create / Update ───────────────────────────────────────────────

class EvaluationCreate(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    evaluator: Optional[str] = None  # Future: populated from JWT claims

    computational_intelligence: ComputationalIntelligenceKPIs = ComputationalIntelligenceKPIs()
    accuracy: AccuracyKPIs = AccuracyKPIs()
    reliability: ReliabilityKPIs = ReliabilityKPIs()
    economics: EconomicsKPIs = EconomicsKPIs()


class EvaluationUpdate(BaseModel):
    agent_name: Optional[str] = Field(None, min_length=1, max_length=255)
    agent_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

    computational_intelligence: Optional[ComputationalIntelligenceKPIs] = None
    accuracy: Optional[AccuracyKPIs] = None
    reliability: Optional[ReliabilityKPIs] = None
    economics: Optional[EconomicsKPIs] = None


# ─── Evaluation Read ──────────────────────────────────────────────────────────

class EvaluationRead(BaseModel):
    id: int
    agent_name: str
    agent_type: str
    description: Optional[str]
    evaluator: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    weight_c: float
    weight_a: float
    weight_r: float
    weight_e: float

    score_c: Optional[float]
    score_a: Optional[float]
    score_r: Optional[float]
    score_e: Optional[float]
    care_score: Optional[float]
    recommendation: Optional[str]

    # C KPIs
    relevance_score: Optional[float]
    reasoning_quality: Optional[float]
    completeness: Optional[float]
    tool_selection_accuracy: Optional[float]
    planning_success_rate: Optional[float]
    task_decomposition_accuracy: Optional[float]
    recommendation_acceptance_rate: Optional[float]

    # A KPIs
    task_success_rate: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    hallucination_rate: Optional[float]
    goal_completion_rate: Optional[float]

    # R KPIs
    failure_rate: Optional[float]
    retry_rate: Optional[float]
    tool_success_rate: Optional[float]
    latency_ms: Optional[float]
    consistency_score: Optional[float]
    error_recovery_rate: Optional[float]
    safety_violation_rate: Optional[float]
    policy_compliance_score: Optional[float]
    audit_coverage: Optional[float]
    pii_leakage_rate: Optional[float]

    # E KPIs
    cost_per_task: Optional[float]
    token_consumption: Optional[float]
    throughput: Optional[float]
    resource_utilization: Optional[float]
    human_effort_saved: Optional[float]
    productivity_improvement: Optional[float]
    business_roi: Optional[float]
    payback_period_months: Optional[float]
    cost_per_successful_task: Optional[float]

    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    recommendations: Optional[List[Dict[str, Any]]]
    kpi_scores: Optional[Dict[str, float]]

    class Config:
        from_attributes = True


class EvaluationSummary(BaseModel):
    """Lightweight summary for list views."""
    id: int
    agent_name: str
    agent_type: str
    care_score: Optional[float]
    score_c: Optional[float]
    score_a: Optional[float]
    score_r: Optional[float]
    score_e: Optional[float]
    recommendation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Comparison ───────────────────────────────────────────────────────────────

class ComparisonRequest(BaseModel):
    evaluation_ids: List[int] = Field(..., min_items=2, max_items=5)


class DimensionComparison(BaseModel):
    dimension: str
    scores: Dict[str, float]  # agent_name -> score
    winner: str


class ComparisonResult(BaseModel):
    agents: List[EvaluationSummary]
    dimension_comparisons: List[DimensionComparison]
    care_score_comparison: Dict[str, float]
    overall_winner: str
    kpi_comparison: Dict[str, Dict[str, Optional[float]]]  # kpi -> agent -> value


# ─── Analytics ───────────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    date: str
    care_score: float
    score_c: float
    score_a: float
    score_r: float
    score_e: float
    agent_name: str


class AnalyticsSummary(BaseModel):
    total_evaluations: int
    avg_care_score: float
    avg_score_c: float
    avg_score_a: float
    avg_score_r: float
    avg_score_e: float
    production_ready_count: int
    not_recommended_count: int
    trend: List[TrendPoint]
    score_distribution: Dict[str, int]  # bucket -> count
    top_agents: List[EvaluationSummary]


# ─── Auth Scaffold ────────────────────────────────────────────────────────────
# These schemas are stubs, ready to be populated when JWT auth is added.

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "viewer"  # viewer | analyst | admin


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Scaffold – will contain access_token when JWT auth is implemented."""
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserRead] = None
    message: str = "Authentication scaffold – JWT not yet implemented"
