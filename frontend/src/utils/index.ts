/**
 * Utility helper functions for the CARE Evaluator frontend.
 */
import type { EvaluationFormData } from '../types';

/**
 * Format a number as a CARE score (1 decimal place).
 */
export function formatScore(score: number | undefined | null): string {
  if (score == null) return 'N/A';
  return score.toFixed(1);
}

/**
 * Get a CSS color class based on score value.
 */
export function getScoreColor(score: number | undefined | null): string {
  if (score == null) return 'text-slate-400';
  if (score >= 90) return 'text-emerald-400';
  if (score >= 80) return 'text-blue-400';
  if (score >= 70) return 'text-amber-400';
  return 'text-red-400';
}

/**
 * Get a hex color based on score value (for charts).
 */
export function getScoreHex(score: number | undefined | null): string {
  if (score == null) return '#64748B';
  if (score >= 90) return '#10B981';
  if (score >= 80) return '#3B82F6';
  if (score >= 70) return '#F59E0B';
  return '#EF4444';
}

/**
 * Get recommendation badge class.
 */
export function getRecommendationBadge(recommendation: string | undefined): string {
  switch (recommendation) {
    case 'Production Ready': return 'badge-production';
    case 'Pilot and Scale': return 'badge-pilot';
    case 'Needs Improvement': return 'badge-improve';
    case 'Not Recommended': return 'badge-not-recommended';
    default: return 'badge bg-slate-700 text-slate-300';
  }
}

/**
 * Get recommendation color for UI accents.
 */
export function getRecommendationColor(recommendation: string | undefined): string {
  switch (recommendation) {
    case 'Production Ready': return '#10B981';
    case 'Pilot and Scale': return '#3B82F6';
    case 'Needs Improvement': return '#F59E0B';
    case 'Not Recommended': return '#EF4444';
    default: return '#64748B';
  }
}

/**
 * Format a date string to a readable format.
 */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

/**
 * Format a date to include time.
 */
export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/**
 * Convert EvaluationFormData (all string fields) into a structured
 * EvaluationCreate payload for the API.
 */
export function buildEvaluationPayload(form: EvaluationFormData) {
  const num = (v?: string) => v && v !== '' ? parseFloat(v) : undefined;

  return {
    agent_name: form.agent_name,
    agent_type: form.agent_type,
    description: form.description || undefined,
    evaluator: form.evaluator || undefined,
    computational_intelligence: {
      relevance_score: num(form.relevance_score),
      reasoning_quality: num(form.reasoning_quality),
      completeness: num(form.completeness),
      tool_selection_accuracy: num(form.tool_selection_accuracy),
      planning_success_rate: num(form.planning_success_rate),
      task_decomposition_accuracy: num(form.task_decomposition_accuracy),
      recommendation_acceptance_rate: num(form.recommendation_acceptance_rate),
    },
    accuracy: {
      task_success_rate: num(form.task_success_rate),
      precision: num(form.precision),
      recall: num(form.recall),
      hallucination_rate: num(form.hallucination_rate),
      goal_completion_rate: num(form.goal_completion_rate),
    },
    reliability: {
      failure_rate: num(form.failure_rate),
      retry_rate: num(form.retry_rate),
      tool_success_rate: num(form.tool_success_rate),
      latency_ms: num(form.latency_ms),
      consistency_score: num(form.consistency_score),
      error_recovery_rate: num(form.error_recovery_rate),
      safety_violation_rate: num(form.safety_violation_rate),
      policy_compliance_score: num(form.policy_compliance_score),
      audit_coverage: num(form.audit_coverage),
      pii_leakage_rate: num(form.pii_leakage_rate),
    },
    economics: {
      cost_per_task: num(form.cost_per_task),
      token_consumption: num(form.token_consumption),
      throughput: num(form.throughput),
      resource_utilization: num(form.resource_utilization),
      human_effort_saved: num(form.human_effort_saved),
      productivity_improvement: num(form.productivity_improvement),
      business_roi: num(form.business_roi),
      payback_period_months: num(form.payback_period_months),
      cost_per_successful_task: num(form.cost_per_successful_task),
    },
  };
}

/**
 * Clamp a value to [min, max].
 */
export function clamp(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, value));
}

/**
 * Calculate gauge stroke-dashoffset for a semi-circle gauge.
 * circumference = π × r for a semi-circle
 */
export function gaugeOffset(score: number, circumference = 283): number {
  return circumference - (score / 100) * circumference;
}

/**
 * Truncate a string to max length.
 */
export function truncate(str: string, max = 80): string {
  return str.length > max ? str.slice(0, max) + '...' : str;
}
