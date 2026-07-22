/**
 * API Service Layer
 * All backend communication goes through this module.
 * Uses Axios with typed responses.
 */
import axios from 'axios';
import type {
  Evaluation, EvaluationSummary, WeightConfig,
  ComparisonResult, AnalyticsSummary,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Request/Response interceptors ─────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

// ── Evaluations ───────────────────────────────────────────────────────────────

export interface ListParams {
  search?: string;
  agent_type?: string;
  recommendation?: string;
  sort_by?: 'created_at' | 'care_score' | 'agent_name';
  sort_order?: 'asc' | 'desc';
  skip?: number;
  limit?: number;
}

export const evaluationsApi = {
  list: async (params?: ListParams): Promise<EvaluationSummary[]> => {
    const { data } = await api.get('/evaluations/', { params });
    return data;
  },

  get: async (id: number): Promise<Evaluation> => {
    const { data } = await api.get(`/evaluations/${id}`);
    return data;
  },

  create: async (payload: Record<string, unknown>): Promise<Evaluation> => {
    const { data } = await api.post('/evaluations/', payload);
    return data;
  },

  update: async (id: number, payload: Record<string, unknown>): Promise<Evaluation> => {
    const { data } = await api.put(`/evaluations/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/evaluations/${id}`);
  },

  duplicate: async (id: number): Promise<Evaluation> => {
    const { data } = await api.post(`/evaluations/${id}/duplicate`);
    return data;
  },
};

// ── Comparison ────────────────────────────────────────────────────────────────

export const comparisonApi = {
  compare: async (evaluation_ids: number[]): Promise<ComparisonResult> => {
    const { data } = await api.post('/comparison/', { evaluation_ids });
    return data;
  },
};

// ── Analytics ─────────────────────────────────────────────────────────────────

export const analyticsApi = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const { data } = await api.get('/analytics/summary');
    return data;
  },
};

// ── Config ────────────────────────────────────────────────────────────────────

export const configApi = {
  getWeights: async (): Promise<WeightConfig> => {
    const { data } = await api.get('/config/weights');
    return data;
  },

  updateWeights: async (weights: {
    weight_c: number; weight_a: number; weight_r: number; weight_e: number;
  }): Promise<WeightConfig> => {
    const { data } = await api.put('/config/weights', weights);
    return data;
  },
};

// ── Utilities ─────────────────────────────────────────────────────────────────

export const utilsApi = {
  seed: async () => {
    const { data } = await api.post('/utils/seed');
    return data;
  },

  exportCsv: () => {
    window.open('/api/utils/export/csv', '_blank');
  },
};

export default api;
