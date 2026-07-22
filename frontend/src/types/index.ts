// ─── CARE Dimension Types ──────────────────────────────────────────────────────

export type DimensionKey = 'c' | 'a' | 'r' | 'e';

export const DIMENSION_INFO = {
  c: { label: 'Computational Intelligence', short: 'C', color: '#6366F1', lightColor: '#818CF8', bg: 'bg-indigo-900/30', text: 'text-indigo-300', border: 'border-indigo-700/50' },
  a: { label: 'Accuracy', short: 'A', color: '#10B981', lightColor: '#34D399', bg: 'bg-emerald-900/30', text: 'text-emerald-300', border: 'border-emerald-700/50' },
  r: { label: 'Reliability', short: 'R', color: '#F59E0B', lightColor: '#FCD34D', bg: 'bg-amber-900/30', text: 'text-amber-300', border: 'border-amber-700/50' },
  e: { label: 'Economics', short: 'E', color: '#3B82F6', lightColor: '#60A5FA', bg: 'bg-blue-900/30', text: 'text-blue-300', border: 'border-blue-700/50' },
} as const;

export const RECOMMENDATION_INFO = {
  'Production Ready': { badge: 'badge-production', color: '#10B981', icon: '✅' },
  'Pilot and Scale': { badge: 'badge-pilot', color: '#3B82F6', icon: '🚀' },
  'Needs Improvement': { badge: 'badge-improve', color: '#F59E0B', icon: '⚠️' },
  'Not Recommended': { badge: 'badge-not-recommended', color: '#EF4444', icon: '❌' },
  'Insufficient Data': { badge: 'badge', color: '#64748B', icon: '❓' },
} as const;

// ─── KPI Definitions ──────────────────────────────────────────────────────────

export interface KPIDefinition {
  key: string;
  label: string;
  dimension: DimensionKey;
  unit: string;
  tooltip: string;
  lowerIsBetter?: boolean;
  rawUnit?: boolean;
}

export const KPI_DEFINITIONS: KPIDefinition[] = [
  // C
  { key: 'relevance_score', label: 'Relevance Score', dimension: 'c', unit: '/100', tooltip: 'How relevant and on-topic are the agent\'s responses to the input context?' },
  { key: 'reasoning_quality', label: 'Reasoning Quality', dimension: 'c', unit: '/100', tooltip: 'Quality of the agent\'s reasoning chains and logical deductions.' },
  { key: 'completeness', label: 'Completeness', dimension: 'c', unit: '/100', tooltip: 'Does the agent provide complete, thorough responses without missing important details?' },
  { key: 'tool_selection_accuracy', label: 'Tool Selection Accuracy', dimension: 'c', unit: '/100', tooltip: 'How accurately does the agent choose the right tools for each task?' },
  { key: 'planning_success_rate', label: 'Planning Success Rate', dimension: 'c', unit: '/100', tooltip: 'Percentage of multi-step plans successfully executed end-to-end.' },
  { key: 'task_decomposition_accuracy', label: 'Task Decomposition Accuracy', dimension: 'c', unit: '/100', tooltip: 'Accuracy of breaking complex tasks into correct subtasks.' },
  { key: 'recommendation_acceptance_rate', label: 'Recommendation Acceptance Rate', dimension: 'c', unit: '/100', tooltip: 'Rate at which human reviewers accept the agent\'s recommendations.' },
  // A
  { key: 'task_success_rate', label: 'Task Success Rate', dimension: 'a', unit: '/100', tooltip: 'Percentage of tasks successfully completed by the agent.' },
  { key: 'precision', label: 'Precision', dimension: 'a', unit: '/100', tooltip: 'Of the agent\'s positive predictions, what fraction are correct?' },
  { key: 'recall', label: 'Recall', dimension: 'a', unit: '/100', tooltip: 'Of all actual positives, what fraction did the agent correctly identify?' },
  { key: 'hallucination_rate', label: 'Hallucination Rate', dimension: 'a', unit: '/100', tooltip: 'Percentage of responses containing fabricated or incorrect information. Lower is better.', lowerIsBetter: true },
  { key: 'goal_completion_rate', label: 'Goal Completion Rate', dimension: 'a', unit: '/100', tooltip: 'Percentage of user-defined goals that the agent fully achieves.' },
  // R
  { key: 'failure_rate', label: 'Failure Rate', dimension: 'r', unit: '/100', tooltip: 'Percentage of tasks that result in a failure or error. Lower is better.', lowerIsBetter: true },
  { key: 'retry_rate', label: 'Retry Rate', dimension: 'r', unit: '/100', tooltip: 'Percentage of tasks that require a retry due to failure. Lower is better.', lowerIsBetter: true },
  { key: 'tool_success_rate', label: 'Tool Success Rate', dimension: 'r', unit: '/100', tooltip: 'Percentage of tool calls that succeed without error.' },
  { key: 'latency_ms', label: 'Latency', dimension: 'r', unit: 'ms', tooltip: 'Average response latency in milliseconds. Lower is better.', lowerIsBetter: true, rawUnit: true },
  { key: 'consistency_score', label: 'Consistency Score', dimension: 'r', unit: '/100', tooltip: 'How consistent are responses across similar inputs?' },
  { key: 'error_recovery_rate', label: 'Error Recovery Rate', dimension: 'r', unit: '/100', tooltip: 'Percentage of errors the agent successfully recovers from autonomously.' },
  { key: 'safety_violation_rate', label: 'Safety Violation Rate', dimension: 'r', unit: '/100', tooltip: 'Percentage of responses that violate safety policies. Lower is better.', lowerIsBetter: true },
  { key: 'policy_compliance_score', label: 'Policy Compliance Score', dimension: 'r', unit: '/100', tooltip: 'How well does the agent comply with organizational policies?' },
  { key: 'audit_coverage', label: 'Audit Coverage', dimension: 'r', unit: '/100', tooltip: 'Percentage of agent actions that are captured in audit logs.' },
  { key: 'pii_leakage_rate', label: 'PII Leakage Rate', dimension: 'r', unit: '/100', tooltip: 'Percentage of responses that inadvertently expose PII. Lower is better.', lowerIsBetter: true },
  // E
  { key: 'cost_per_task', label: 'Cost per Task', dimension: 'e', unit: '$', tooltip: 'Average cost in USD per completed task. Lower is better.', lowerIsBetter: true, rawUnit: true },
  { key: 'token_consumption', label: 'Token Consumption', dimension: 'e', unit: 'tokens', tooltip: 'Average token usage per task. Lower is better.', lowerIsBetter: true, rawUnit: true },
  { key: 'throughput', label: 'Throughput', dimension: 'e', unit: 'tasks/hr', tooltip: 'Number of tasks processed per hour. Higher is better.', rawUnit: true },
  { key: 'resource_utilization', label: 'Resource Utilization', dimension: 'e', unit: '/100', tooltip: 'Efficiency of compute resource usage.' },
  { key: 'human_effort_saved', label: 'Human Effort Saved', dimension: 'e', unit: '/100', tooltip: 'Percentage reduction in human effort compared to manual processing.' },
  { key: 'productivity_improvement', label: 'Productivity Improvement', dimension: 'e', unit: '%', tooltip: 'Percentage improvement in team productivity attributable to the agent.', rawUnit: true },
  { key: 'business_roi', label: 'Business ROI', dimension: 'e', unit: '%', tooltip: 'Return on investment of deploying the AI agent.', rawUnit: true },
  { key: 'payback_period_months', label: 'Payback Period', dimension: 'e', unit: 'months', tooltip: 'Time in months to recoup the AI investment. Lower is better.', lowerIsBetter: true, rawUnit: true },
  { key: 'cost_per_successful_task', label: 'Cost per Successful Task', dimension: 'e', unit: '$', tooltip: 'Average cost per successfully completed task (excludes failures). Lower is better.', lowerIsBetter: true, rawUnit: true },
];

// ─── Evaluation Types ──────────────────────────────────────────────────────────

export interface Evaluation {
  id: number;
  agent_name: string;
  agent_type: string;
  description?: string;
  evaluator?: string;
  created_at: string;
  updated_at?: string;

  weight_c: number;
  weight_a: number;
  weight_r: number;
  weight_e: number;

  score_c?: number;
  score_a?: number;
  score_r?: number;
  score_e?: number;
  care_score?: number;
  recommendation?: string;

  // C KPIs
  relevance_score?: number;
  reasoning_quality?: number;
  completeness?: number;
  tool_selection_accuracy?: number;
  planning_success_rate?: number;
  task_decomposition_accuracy?: number;
  recommendation_acceptance_rate?: number;

  // A KPIs
  task_success_rate?: number;
  precision?: number;
  recall?: number;
  hallucination_rate?: number;
  goal_completion_rate?: number;

  // R KPIs
  failure_rate?: number;
  retry_rate?: number;
  tool_success_rate?: number;
  latency_ms?: number;
  consistency_score?: number;
  error_recovery_rate?: number;
  safety_violation_rate?: number;
  policy_compliance_score?: number;
  audit_coverage?: number;
  pii_leakage_rate?: number;

  // E KPIs
  cost_per_task?: number;
  token_consumption?: number;
  throughput?: number;
  resource_utilization?: number;
  human_effort_saved?: number;
  productivity_improvement?: number;
  business_roi?: number;
  payback_period_months?: number;
  cost_per_successful_task?: number;

  strengths?: string[];
  weaknesses?: string[];
  recommendations?: Recommendation[];
  kpi_scores?: Record<string, number>;
}

export interface EvaluationSummary {
  id: number;
  agent_name: string;
  agent_type: string;
  care_score?: number;
  score_c?: number;
  score_a?: number;
  score_r?: number;
  score_e?: number;
  recommendation?: string;
  created_at: string;
}

export interface Recommendation {
  dimension: DimensionKey;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  kpi: string;
}

// ─── Weight Config ─────────────────────────────────────────────────────────────

export interface WeightConfig {
  id: number;
  weight_c: number;
  weight_a: number;
  weight_r: number;
  weight_e: number;
  updated_at?: string;
}

// ─── Comparison Types ──────────────────────────────────────────────────────────

export interface DimensionComparison {
  dimension: string;
  scores: Record<string, number>;
  winner: string;
}

export interface ComparisonResult {
  agents: EvaluationSummary[];
  dimension_comparisons: DimensionComparison[];
  care_score_comparison: Record<string, number>;
  overall_winner: string;
  kpi_comparison: Record<string, Record<string, number | null>>;
}

// ─── Analytics Types ────────────────────────────────────────────────────────────

export interface TrendPoint {
  date: string;
  care_score: number;
  score_c: number;
  score_a: number;
  score_r: number;
  score_e: number;
  agent_name: string;
}

export interface AnalyticsSummary {
  total_evaluations: number;
  avg_care_score: number;
  avg_score_c: number;
  avg_score_a: number;
  avg_score_r: number;
  avg_score_e: number;
  production_ready_count: number;
  not_recommended_count: number;
  trend: TrendPoint[];
  score_distribution: Record<string, number>;
  top_agents: EvaluationSummary[];
}

// ─── Form Types ────────────────────────────────────────────────────────────────

export interface EvaluationFormData {
  agent_name: string;
  agent_type: string;
  description?: string;
  evaluator?: string;
  // C KPIs
  relevance_score?: string;
  reasoning_quality?: string;
  completeness?: string;
  tool_selection_accuracy?: string;
  planning_success_rate?: string;
  task_decomposition_accuracy?: string;
  recommendation_acceptance_rate?: string;
  // A KPIs
  task_success_rate?: string;
  precision?: string;
  recall?: string;
  hallucination_rate?: string;
  goal_completion_rate?: string;
  // R KPIs
  failure_rate?: string;
  retry_rate?: string;
  tool_success_rate?: string;
  latency_ms?: string;
  consistency_score?: string;
  error_recovery_rate?: string;
  safety_violation_rate?: string;
  policy_compliance_score?: string;
  audit_coverage?: string;
  pii_leakage_rate?: string;
  // E KPIs
  cost_per_task?: string;
  token_consumption?: string;
  throughput?: string;
  resource_utilization?: string;
  human_effort_saved?: string;
  productivity_improvement?: string;
  business_roi?: string;
  payback_period_months?: string;
  cost_per_successful_task?: string;
}
