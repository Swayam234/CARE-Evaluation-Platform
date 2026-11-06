// ─── Pipeline Types ──────────────────────────────────────────────────────────
// TypeScript types for the automated evaluation pipeline.
// These match the Pydantic schemas in app/schemas/pipeline.py

export type RunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
export type TraceStatus = 'success' | 'failed' | 'error' | 'unknown';
export type CalculationStatus = 'calculated' | 'unavailable' | 'error';
export type KpiSource = 'telemetry' | 'benchmark' | 'llm_judge' | 'business' | 'evaluator' | 'infrastructure';

export interface EvaluationRun {
  id: number;
  agent_name: string;
  agent_type: string;
  description?: string;
  dataset_name?: string;
  dataset_id?: number;
  total_tasks?: number;
  started_at?: string;
  completed_at?: string;
  status: RunStatus;
  error_message?: string;
  evaluation_id?: number;
  llm_input_cost_per_1k?: number;
  llm_output_cost_per_1k?: number;
  created_at: string;
  updated_at?: string;
}

export interface EvaluationRunSummary {
  id: number;
  agent_name: string;
  agent_type: string;
  status: RunStatus;
  total_tasks?: number;
  dataset_name?: string;
  evaluation_id?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface EvaluationRunCreate {
  agent_name: string;
  agent_type: string;
  description?: string;
  dataset_name?: string;
  dataset_id?: number;
  total_tasks?: number;
  llm_input_cost_per_1k?: number;
  llm_output_cost_per_1k?: number;
}

export interface AgentTrace {
  id: number;
  evaluation_run_id: number;
  trace_id?: string;
  task_id?: string;
  model_name?: string;
  started_at?: string;
  completed_at?: string;
  latency_ms?: number;
  status: TraceStatus;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  error_message?: string;
  retry_count: number;
  created_at: string;
}

export interface KpiMeasurement {
  id: number;
  evaluation_run_id: number;
  kpi_name: string;
  raw_value: number | null;    // null = unavailable – NEVER treat as zero
  unit?: string;
  source?: KpiSource;
  calculation_status: CalculationStatus;
  notes?: string;
  created_at: string;
}

export interface KpiCoverageStats {
  total_kpis: number;
  calculated: number;
  unavailable: number;
  error: number;
  coverage_percent: number;
}

export interface KpiCalculationResponse {
  run_id: number;
  measurements: KpiMeasurement[];
  coverage: KpiCoverageStats;
  message: string;
}

export interface RunStatusResponse {
  run_id: number;
  status: RunStatus;
  agent_name: string;
  total_tasks?: number;
  trace_count: number;
  tool_trace_count: number;
  started_at?: string;
  completed_at?: string;
  evaluation_id?: number;
  error_message?: string;
}

export interface EvaluationDataset {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  test_case_count?: number;
}

export interface SimulationConfig {
  agent_name: string;
  agent_type: string;
  description?: string;
  num_tasks: number;
  success_rate: number;
  avg_latency_ms: number;
  latency_variance_pct: number;
  avg_input_tokens: number;
  avg_output_tokens: number;
  tool_call_rate: number;
  tool_success_rate: number;
  retry_rate: number;
  llm_input_cost_per_1k?: number;
  llm_output_cost_per_1k?: number;
  dataset_id?: number;
  is_simulation: true;
  simulation_label: string;
}

export interface SimulationStartResponse {
  simulation_warning: string;
  run_id: number;
  agent_name: string;
  num_tasks: number;
  status: RunStatus;
  poll_url: string;
  message: string;
}
