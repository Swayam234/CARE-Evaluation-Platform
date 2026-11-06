/**
 * Pipeline API Service Layer
 * All automated evaluation pipeline API calls go through this module.
 * Mirrors the conventions of api.ts.
 */
import axios from 'axios';
import type {
  EvaluationRun, EvaluationRunCreate, EvaluationRunSummary,
  AgentTrace, KpiMeasurement, KpiCalculationResponse,
  RunStatusResponse, EvaluationDataset,
  SimulationConfig, SimulationStartResponse,
} from '../types/pipeline';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

// ── Evaluation Runs ───────────────────────────────────────────────────────────

export const pipelineApi = {
  createRun: async (payload: EvaluationRunCreate): Promise<EvaluationRun> => {
    const { data } = await api.post('/evaluation-runs/', payload);
    return data;
  },

  listRuns: async (statusFilter?: string): Promise<EvaluationRunSummary[]> => {
    const { data } = await api.get('/evaluation-runs/', {
      params: statusFilter ? { status: statusFilter } : undefined,
    });
    return data;
  },

  getRun: async (runId: number): Promise<EvaluationRun> => {
    const { data } = await api.get(`/evaluation-runs/${runId}`);
    return data;
  },

  getStatus: async (runId: number): Promise<RunStatusResponse> => {
    const { data } = await api.get(`/evaluation-runs/${runId}/status`);
    return data;
  },

  deleteRun: async (runId: number): Promise<void> => {
    await api.delete(`/evaluation-runs/${runId}`);
  },

  getTraces: async (runId: number, limit = 100): Promise<AgentTrace[]> => {
    const { data } = await api.get(`/evaluation-runs/${runId}/traces`, { params: { limit } });
    return data;
  },

  completeRun: async (runId: number): Promise<EvaluationRun> => {
    const { data } = await api.post(`/evaluation-runs/${runId}/complete`);
    return data;
  },

  triggerKpiCalculation: async (runId: number) => {
    const { data } = await api.post(`/evaluation-runs/${runId}/calculate-kpis`);
    return data;
  },

  getKpis: async (runId: number): Promise<KpiCalculationResponse> => {
    const { data } = await api.get(`/evaluation-runs/${runId}/kpis`);
    return data;
  },

  generateEvaluation: async (runId: number) => {
    const { data } = await api.post(`/evaluation-runs/${runId}/generate-evaluation`);
    return data;
  },
};

// ── Simulation Adapter ────────────────────────────────────────────────────────

export const simulationApi = {
  startSimulation: async (config: Omit<SimulationConfig, 'is_simulation' | 'simulation_label'>): Promise<SimulationStartResponse> => {
    const payload: SimulationConfig = {
      ...config,
      is_simulation: true,
      simulation_label: 'SIMULATED – synthetic traces, not a real agent execution',
    };
    const { data } = await api.post('/simulation/run', payload);
    return data;
  },
};

// ── Datasets ──────────────────────────────────────────────────────────────────

export const datasetsApi = {
  list: async (): Promise<EvaluationDataset[]> => {
    const { data } = await api.get('/datasets/');
    return data;
  },

  create: async (name: string, description?: string): Promise<EvaluationDataset> => {
    const { data } = await api.post('/datasets/', { name, description });
    return data;
  },
};

export default pipelineApi;
