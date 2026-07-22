"""
CARE Scoring Engine
===================
Normalizes raw KPI values onto a 0-100 scale, computes dimension scores,
applies configurable weights, and returns the overall CARE score + deployment
recommendation.

Design notes:
  • KPIs already on 0-100: passed through directly.
  • Inverse KPIs (lower is better): score = 100 - raw_value.
  • KPIs with raw units (latency_ms, cost, tokens): normalised with reference
    baselines that represent "excellent" and "poor" performance.
  • Missing KPIs (None) are excluded from dimension averages so partial
    evaluations still produce valid scores.
"""
from typing import Optional, Dict, Any
from app.models.evaluation import Evaluation
from app.schemas.evaluation import EvaluationCreate, WeightConfigBase


# ── Reference baselines for raw-unit KPIs ────────────────────────────────────
# These represent "excellent" (→100) and "poor" (→0) reference points.
# They can be made configurable in a future iteration.

LATENCY_EXCELLENT_MS = 200      # 200ms response → score 100
LATENCY_POOR_MS = 10_000        # 10s response   → score 0

COST_PER_TASK_EXCELLENT = 0.001  # $0.001/task → score 100
COST_PER_TASK_POOR = 1.00        # $1.00/task  → score 0

TOKENS_EXCELLENT = 500           # 500 tokens/task → score 100
TOKENS_POOR = 50_000             # 50k tokens/task → score 0

THROUGHPUT_EXCELLENT = 1000      # 1000 tasks/hr → score 100
THROUGHPUT_POOR = 1              # 1 task/hr     → score 0

PRODUCTIVITY_EXCELLENT = 200     # 200% improvement → score 100
PRODUCTIVITY_POOR = 0            # 0% → score 0

ROI_EXCELLENT = 500              # 500% ROI → score 100
ROI_POOR = -100                  # -100% ROI → score 0

PAYBACK_EXCELLENT_MONTHS = 1     # 1 month → score 100
PAYBACK_POOR_MONTHS = 60         # 5 years → score 0

COST_SUCCESSFUL_EXCELLENT = 0.002
COST_SUCCESSFUL_POOR = 2.00


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


def _normalize_inverse(raw: float) -> float:
    """Convert an inverse KPI (lower is better, 0-100 input) to 0-100 score."""
    return _clamp(100.0 - raw)


def _normalize_range(raw: float, poor: float, excellent: float) -> float:
    """
    Linear interpolation between poor→0 and excellent→100.
    Works for both ascending (higher=better) and descending (lower=better) metrics.
    """
    if excellent == poor:
        return 50.0
    score = (raw - poor) / (excellent - poor) * 100.0
    return _clamp(score)


def _avg(values: list) -> Optional[float]:
    """Return average of non-None values; None if list is empty."""
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


def normalize_kpis(data: EvaluationCreate) -> Dict[str, float]:
    """
    Normalize every KPI to a 0-100 score.
    Returns a flat dict of kpi_name → normalized_score (only for provided KPIs).
    """
    scores: Dict[str, float] = {}
    ci = data.computational_intelligence
    acc = data.accuracy
    rel = data.reliability
    eco = data.economics

    # ── Computational Intelligence ────────────────────────────────────────────
    if ci.relevance_score is not None:
        scores["relevance_score"] = _clamp(ci.relevance_score)
    if ci.reasoning_quality is not None:
        scores["reasoning_quality"] = _clamp(ci.reasoning_quality)
    if ci.completeness is not None:
        scores["completeness"] = _clamp(ci.completeness)
    if ci.tool_selection_accuracy is not None:
        scores["tool_selection_accuracy"] = _clamp(ci.tool_selection_accuracy)
    if ci.planning_success_rate is not None:
        scores["planning_success_rate"] = _clamp(ci.planning_success_rate)
    if ci.task_decomposition_accuracy is not None:
        scores["task_decomposition_accuracy"] = _clamp(ci.task_decomposition_accuracy)
    if ci.recommendation_acceptance_rate is not None:
        scores["recommendation_acceptance_rate"] = _clamp(ci.recommendation_acceptance_rate)

    # ── Accuracy ─────────────────────────────────────────────────────────────
    if acc.task_success_rate is not None:
        scores["task_success_rate"] = _clamp(acc.task_success_rate)
    if acc.precision is not None:
        scores["precision"] = _clamp(acc.precision)
    if acc.recall is not None:
        scores["recall"] = _clamp(acc.recall)
    if acc.hallucination_rate is not None:
        scores["hallucination_rate"] = _normalize_inverse(acc.hallucination_rate)  # lower is better
    if acc.goal_completion_rate is not None:
        scores["goal_completion_rate"] = _clamp(acc.goal_completion_rate)

    # ── Reliability ───────────────────────────────────────────────────────────
    if rel.failure_rate is not None:
        scores["failure_rate"] = _normalize_inverse(rel.failure_rate)
    if rel.retry_rate is not None:
        scores["retry_rate"] = _normalize_inverse(rel.retry_rate)
    if rel.tool_success_rate is not None:
        scores["tool_success_rate"] = _clamp(rel.tool_success_rate)
    if rel.latency_ms is not None:
        scores["latency_ms"] = _normalize_range(rel.latency_ms, LATENCY_POOR_MS, LATENCY_EXCELLENT_MS)
    if rel.consistency_score is not None:
        scores["consistency_score"] = _clamp(rel.consistency_score)
    if rel.error_recovery_rate is not None:
        scores["error_recovery_rate"] = _clamp(rel.error_recovery_rate)
    if rel.safety_violation_rate is not None:
        scores["safety_violation_rate"] = _normalize_inverse(rel.safety_violation_rate)
    if rel.policy_compliance_score is not None:
        scores["policy_compliance_score"] = _clamp(rel.policy_compliance_score)
    if rel.audit_coverage is not None:
        scores["audit_coverage"] = _clamp(rel.audit_coverage)
    if rel.pii_leakage_rate is not None:
        scores["pii_leakage_rate"] = _normalize_inverse(rel.pii_leakage_rate)

    # ── Economics ─────────────────────────────────────────────────────────────
    if eco.cost_per_task is not None:
        scores["cost_per_task"] = _normalize_range(eco.cost_per_task, COST_PER_TASK_POOR, COST_PER_TASK_EXCELLENT)
    if eco.token_consumption is not None:
        scores["token_consumption"] = _normalize_range(eco.token_consumption, TOKENS_POOR, TOKENS_EXCELLENT)
    if eco.throughput is not None:
        scores["throughput"] = _normalize_range(eco.throughput, THROUGHPUT_POOR, THROUGHPUT_EXCELLENT)
    if eco.resource_utilization is not None:
        scores["resource_utilization"] = _clamp(eco.resource_utilization)
    if eco.human_effort_saved is not None:
        scores["human_effort_saved"] = _clamp(eco.human_effort_saved)
    if eco.productivity_improvement is not None:
        scores["productivity_improvement"] = _normalize_range(
            eco.productivity_improvement, PRODUCTIVITY_POOR, PRODUCTIVITY_EXCELLENT
        )
    if eco.business_roi is not None:
        scores["business_roi"] = _normalize_range(eco.business_roi, ROI_POOR, ROI_EXCELLENT)
    if eco.payback_period_months is not None:
        scores["payback_period_months"] = _normalize_range(
            eco.payback_period_months, PAYBACK_POOR_MONTHS, PAYBACK_EXCELLENT_MONTHS
        )
    if eco.cost_per_successful_task is not None:
        scores["cost_per_successful_task"] = _normalize_range(
            eco.cost_per_successful_task, COST_SUCCESSFUL_POOR, COST_SUCCESSFUL_EXCELLENT
        )

    return {k: round(v, 2) for k, v in scores.items()}


# ── KPI → Dimension mapping ───────────────────────────────────────────────────
C_KPIS = [
    "relevance_score", "reasoning_quality", "completeness",
    "tool_selection_accuracy", "planning_success_rate",
    "task_decomposition_accuracy", "recommendation_acceptance_rate",
]
A_KPIS = [
    "task_success_rate", "precision", "recall",
    "hallucination_rate", "goal_completion_rate",
]
R_KPIS = [
    "failure_rate", "retry_rate", "tool_success_rate", "latency_ms",
    "consistency_score", "error_recovery_rate", "safety_violation_rate",
    "policy_compliance_score", "audit_coverage", "pii_leakage_rate",
]
E_KPIS = [
    "cost_per_task", "token_consumption", "throughput", "resource_utilization",
    "human_effort_saved", "productivity_improvement", "business_roi",
    "payback_period_months", "cost_per_successful_task",
]


def compute_dimension_scores(kpi_scores: Dict[str, float]):
    """Average KPI scores per dimension. Returns (score_c, score_a, score_r, score_e)."""
    score_c = _avg([kpi_scores.get(k) for k in C_KPIS])
    score_a = _avg([kpi_scores.get(k) for k in A_KPIS])
    score_r = _avg([kpi_scores.get(k) for k in R_KPIS])
    score_e = _avg([kpi_scores.get(k) for k in E_KPIS])
    return score_c, score_a, score_r, score_e


def compute_care_score(
    score_c: Optional[float],
    score_a: Optional[float],
    score_r: Optional[float],
    score_e: Optional[float],
    weights: WeightConfigBase,
) -> Optional[float]:
    """
    Compute the overall CARE score using the configured weights.
    Only includes dimensions that have a computed score (partial evaluations supported).
    """
    total_weight = 0.0
    weighted_sum = 0.0

    if score_c is not None:
        weighted_sum += score_c * weights.weight_c
        total_weight += weights.weight_c
    if score_a is not None:
        weighted_sum += score_a * weights.weight_a
        total_weight += weights.weight_a
    if score_r is not None:
        weighted_sum += score_r * weights.weight_r
        total_weight += weights.weight_r
    if score_e is not None:
        weighted_sum += score_e * weights.weight_e
        total_weight += weights.weight_e

    if total_weight == 0:
        return None

    # Normalize to full weight basis so partial evals don't get artificially penalised
    return round(weighted_sum / total_weight, 2)


def get_deployment_recommendation(care_score: Optional[float]) -> str:
    """Map CARE score to a deployment recommendation tier."""
    if care_score is None:
        return "Insufficient Data"
    if care_score >= 90:
        return "Production Ready"
    elif care_score >= 80:
        return "Pilot and Scale"
    elif care_score >= 70:
        return "Needs Improvement"
    else:
        return "Not Recommended"


def run_scoring(data: EvaluationCreate, weights: WeightConfigBase) -> Dict[str, Any]:
    """
    End-to-end scoring pipeline.
    Returns a dict with kpi_scores, dimension scores, care_score, recommendation.
    """
    kpi_scores = normalize_kpis(data)
    score_c, score_a, score_r, score_e = compute_dimension_scores(kpi_scores)
    care_score = compute_care_score(score_c, score_a, score_r, score_e, weights)
    recommendation = get_deployment_recommendation(care_score)

    return {
        "kpi_scores": kpi_scores,
        "score_c": score_c,
        "score_a": score_a,
        "score_r": score_r,
        "score_e": score_e,
        "care_score": care_score,
        "recommendation": recommendation,
    }
