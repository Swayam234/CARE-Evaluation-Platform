/**
 * AutomatedEvaluation Page
 * Full end-to-end automated evaluation workflow:
 *   Step 1 → Configure simulation
 *   Step 2 → Monitor run status (async polling)
 *   Step 3 → KPI measurements with source transparency + coverage indicator
 *   Step 4 → CARE Score results (reuses existing components)
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot, Play, Loader2, CheckCircle2, XCircle, Clock, AlertTriangle,
  Zap, Database, BarChart3, ChevronRight, Info, RefreshCw, ExternalLink,
  Activity, Shield, Brain, DollarSign, Target, Cpu,
} from 'lucide-react';
import { clsx } from 'clsx';
import { toast } from 'react-toastify';
import { simulationApi, pipelineApi } from '../services/pipelineApi';
import { evaluationsApi } from '../services/api';
import type { RunStatusResponse, KpiMeasurement, KpiCoverageStats } from '../types/pipeline';
import type { Evaluation } from '../types';
import CAREScoreGauge from '../components/CAREScoreGauge';
import DimensionCard from '../components/DimensionCard';
import RecommendationCard from '../components/RecommendationCard';
import { DIMENSION_INFO } from '../types';

const AGENT_TYPES = [
  'Chatbot', 'RAG Agent', 'Coding Assistant', 'Workflow Automation',
  'Customer Support', 'Sales Agent', 'HR Agent', 'Finance Agent', 'Research Agent', 'Other',
];

const KPI_SOURCE_META: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  telemetry:      { label: 'Telemetry',      color: '#6366F1', icon: <Activity size={11} /> },
  benchmark:      { label: 'Benchmark',      color: '#10B981', icon: <Target size={11} /> },
  llm_judge:      { label: 'LLM Judge',      color: '#F59E0B', icon: <Brain size={11} /> },
  evaluator:      { label: 'Evaluator',      color: '#3B82F6', icon: <Shield size={11} /> },
  business:       { label: 'Business',       color: '#8B5CF6', icon: <DollarSign size={11} /> },
  infrastructure: { label: 'Infrastructure', color: '#64748B', icon: <Cpu size={11} /> },
};

type Step = 'configure' | 'running' | 'kpis' | 'results';

// ── Source Badge ──────────────────────────────────────────────────────────────
const SourceBadge: React.FC<{ source?: string; status: string }> = ({ source, status }) => {
  if (status === 'unavailable') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-500 border border-slate-700">
        <XCircle size={10} /> Unavailable
      </span>
    );
  }
  if (status === 'error') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-900/30 text-red-400 border border-red-700/30">
        <AlertTriangle size={10} /> Error
      </span>
    );
  }
  const meta = source ? KPI_SOURCE_META[source] : null;
  if (!meta) return null;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border"
      style={{ backgroundColor: `${meta.color}15`, color: meta.color, borderColor: `${meta.color}30` }}
    >
      {meta.icon} {meta.label}
    </span>
  );
};

// ── Coverage Bar ──────────────────────────────────────────────────────────────
const CoverageBar: React.FC<{ coverage: KpiCoverageStats }> = ({ coverage }) => (
  <div className="card p-4 space-y-3">
    <div className="flex items-center justify-between">
      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">KPI Coverage</p>
      <span className="text-lg font-black text-slate-100">{coverage.coverage_percent.toFixed(0)}%</span>
    </div>
    <div className="w-full h-2 bg-bg-hover rounded-full overflow-hidden">
      <div className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-700"
           style={{ width: `${coverage.coverage_percent}%` }} />
    </div>
    <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
      <div className="card p-2 border-emerald-700/30">
        <p className="text-emerald-400 font-bold text-sm">{coverage.calculated}</p>
        <p className="text-slate-500">Calculated</p>
      </div>
      <div className="card p-2 border-slate-700/30">
        <p className="text-slate-500 font-bold text-sm">{coverage.unavailable}</p>
        <p className="text-slate-500">Unavailable</p>
      </div>
      <div className="card p-2 border-red-700/30">
        <p className="text-red-400 font-bold text-sm">{coverage.error}</p>
        <p className="text-slate-500">Error</p>
      </div>
    </div>
    <p className="text-[10px] text-slate-600 italic">
      Unavailable KPIs require LLM judge, safety evaluator, or business data.
      They are never treated as zero.
    </p>
  </div>
);

// ── Status Badge ──────────────────────────────────────────────────────────────
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, string> = {
    PENDING: 'bg-slate-800 text-slate-400 border-slate-700',
    RUNNING: 'bg-indigo-900/30 text-indigo-300 border-indigo-700/30',
    COMPLETED: 'bg-emerald-900/30 text-emerald-300 border-emerald-700/30',
    FAILED: 'bg-red-900/30 text-red-300 border-red-700/30',
  };
  return (
    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-bold border', map[status] || map.PENDING)}>
      {status}
    </span>
  );
};

// ── Main Component ────────────────────────────────────────────────────────────
const AutomatedEvaluation: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('configure');
  const [submitting, setSubmitting] = useState(false);
  const [runId, setRunId] = useState<number | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [kpiData, setKpiData] = useState<{ measurements: KpiMeasurement[]; coverage: KpiCoverageStats } | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Form state
  const [form, setForm] = useState({
    agent_name: '',
    agent_type: 'RAG Agent',
    num_tasks: 20,
    success_rate: 0.85,
    avg_latency_ms: 750,
    latency_variance_pct: 0.3,
    tool_call_rate: 0.7,
    tool_success_rate: 0.92,
    retry_rate: 0.08,
    avg_input_tokens: 600,
    avg_output_tokens: 350,
    llm_input_cost_per_1k: 0.0005,
    llm_output_cost_per_1k: 0.0015,
  });

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const pollStatus = useCallback(async (id: number) => {
    try {
      const status = await pipelineApi.getStatus(id);
      setRunStatus(status);

      if (status.status === 'COMPLETED' || status.status === 'FAILED') {
        stopPolling();
        if (status.status === 'COMPLETED' && status.evaluation_id) {
          // Fetch KPIs
          try {
            const kpiRes = await pipelineApi.getKpis(id);
            setKpiData({ measurements: kpiRes.measurements, coverage: kpiRes.coverage });
            setStep('kpis');
          } catch { /* handled below */ }
          // Fetch Evaluation
          try {
            const ev = await evaluationsApi.get(status.evaluation_id);
            setEvaluation(ev);
          } catch { toast.error('Could not load evaluation results'); }
        } else if (status.status === 'FAILED') {
          toast.error(`Evaluation run failed: ${status.error_message || 'Unknown error'}`);
        }
      }
    } catch (e) {
      console.error('Status poll error:', e);
    }
  }, []);

  useEffect(() => {
    if (runId && step === 'running') {
      pollStatus(runId);
      pollRef.current = setInterval(() => pollStatus(runId), 2000);
    }
    return stopPolling;
  }, [runId, step, pollStatus]);

  const handleStart = async () => {
    if (!form.agent_name.trim()) { toast.error('Agent name is required'); return; }
    setSubmitting(true);
    try {
      const res = await simulationApi.startSimulation(form);
      setRunId(res.run_id);
      setStep('running');
      toast.info(`⚡ Simulation started – Run #${res.run_id}`);
    } catch (e: any) {
      toast.error(e.message || 'Failed to start simulation');
    } finally {
      setSubmitting(false);
    }
  };

  const elapsedSeconds = runStatus?.started_at && runStatus?.completed_at
    ? Math.round((new Date(runStatus.completed_at).getTime() - new Date(runStatus.started_at).getTime()) / 1000)
    : null;

  // ── Step: Configure ──────────────────────────────────────────────────────
  if (step === 'configure') return (
    <div className="max-w-4xl mx-auto animate-fade-in space-y-6">
      {/* Header */}
      <div className="card-glass p-5">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Zap size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100">Automated Evaluation</h1>
            <p className="text-xs text-slate-500">Simulate agent execution → compute KPIs → generate CARE Score</p>
          </div>
        </div>
        <div className="mt-3 p-3 rounded-lg bg-amber-900/20 border border-amber-700/30 flex items-start gap-2">
          <AlertTriangle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-amber-300">
            <strong>Simulation Mode:</strong> This demo uses synthetic traces. 
            To evaluate a real agent, POST traces to <code className="text-amber-200">/api/evaluation-runs/&#123;id&#125;/traces</code>.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Form */}
        <div className="lg:col-span-2 card p-6 space-y-5">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-widest">Agent Configuration</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Agent Name *</label>
              <input id="auto-agent-name" className="input" placeholder="e.g. Customer Support Agent v2"
                value={form.agent_name} onChange={e => setForm(f => ({ ...f, agent_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Agent Type</label>
              <select id="auto-agent-type" className="input" value={form.agent_type}
                onChange={e => setForm(f => ({ ...f, agent_type: e.target.value }))}>
                {AGENT_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="border-t border-bg-border pt-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Simulation Parameters</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { key: 'num_tasks', label: 'Tasks', min: 1, max: 1000, step: 1 },
                { key: 'success_rate', label: 'Success Rate', min: 0, max: 1, step: 0.05 },
                { key: 'avg_latency_ms', label: 'Avg Latency (ms)', min: 50, max: 30000, step: 50 },
                { key: 'tool_call_rate', label: 'Tool Call Rate', min: 0, max: 1, step: 0.05 },
                { key: 'tool_success_rate', label: 'Tool Success Rate', min: 0, max: 1, step: 0.05 },
                { key: 'retry_rate', label: 'Retry Rate', min: 0, max: 1, step: 0.01 },
                { key: 'avg_input_tokens', label: 'Avg Input Tokens', min: 10, max: 50000, step: 50 },
                { key: 'avg_output_tokens', label: 'Avg Output Tokens', min: 10, max: 10000, step: 50 },
              ].map(({ key, label, min, max, step: s }) => (
                <div key={key}>
                  <label className="label text-xs">{label}</label>
                  <input type="number" className="input text-sm" min={min} max={max} step={s}
                    value={form[key as keyof typeof form]}
                    onChange={e => setForm(f => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))} />
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-bg-border pt-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Cost Configuration (optional)</h3>
            <p className="text-[11px] text-slate-500 mb-3">
              Set token costs to enable cost_per_task KPI calculation. Leave at 0 to mark as unavailable.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label text-xs">Input Cost / 1K tokens ($)</label>
                <input type="number" step="0.0001" className="input text-sm"
                  value={form.llm_input_cost_per_1k}
                  onChange={e => setForm(f => ({ ...f, llm_input_cost_per_1k: parseFloat(e.target.value) || 0 }))} />
              </div>
              <div>
                <label className="label text-xs">Output Cost / 1K tokens ($)</label>
                <input type="number" step="0.0001" className="input text-sm"
                  value={form.llm_output_cost_per_1k}
                  onChange={e => setForm(f => ({ ...f, llm_output_cost_per_1k: parseFloat(e.target.value) || 0 }))} />
              </div>
            </div>
          </div>

          <button id="start-simulation-btn" onClick={handleStart} disabled={submitting}
            className="btn-primary w-full justify-center text-sm">
            {submitting ? <><Loader2 size={16} className="animate-spin" /> Starting…</> : <><Play size={16} /> Start Automated Evaluation</>}
          </button>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">What happens</p>
            {[
              { icon: <Zap size={14} className="text-indigo-400" />, text: 'Synthetic traces generated' },
              { icon: <Activity size={14} className="text-amber-400" />, text: '8 telemetry KPIs calculated' },
              { icon: <Brain size={14} className="text-indigo-400" />, text: 'CARE scoring engine runs' },
              { icon: <Target size={14} className="text-emerald-400" />, text: 'Recommendations generated' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-slate-400">
                {item.icon} {item.text}
              </div>
            ))}
          </div>
          <div className="card p-4 space-y-2">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">KPI Sources</p>
            {Object.entries(KPI_SOURCE_META).map(([key, meta]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] border"
                  style={{ backgroundColor: `${meta.color}15`, color: meta.color, borderColor: `${meta.color}30` }}>
                  {meta.icon} {meta.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // ── Step: Running ─────────────────────────────────────────────────────────
  if (step === 'running') return (
    <div className="max-w-2xl mx-auto animate-fade-in space-y-6">
      <div className="card-glass p-6 text-center space-y-4">
        <div className="flex justify-center">
          {runStatus?.status === 'FAILED' ? (
            <XCircle size={48} className="text-red-400" />
          ) : runStatus?.status === 'COMPLETED' ? (
            <CheckCircle2 size={48} className="text-emerald-400" />
          ) : (
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-indigo-500/30 border-t-indigo-500 animate-spin" />
              <Bot size={20} className="absolute inset-0 m-auto text-indigo-400" />
            </div>
          )}
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100">
            {runStatus?.status === 'COMPLETED' ? 'Evaluation Complete!' :
             runStatus?.status === 'FAILED' ? 'Evaluation Failed' : 'Running Evaluation…'}
          </h2>
          <p className="text-sm text-slate-500 mt-1">Run #{runId} · {runStatus?.agent_name}</p>
        </div>

        <div className="grid grid-cols-3 gap-3 text-center">
          {[
            { label: 'Status', value: <StatusBadge status={runStatus?.status || 'PENDING'} /> },
            { label: 'Traces', value: <span className="font-bold text-slate-200">{runStatus?.trace_count ?? '–'}</span> },
            { label: 'Tool Calls', value: <span className="font-bold text-slate-200">{runStatus?.tool_trace_count ?? '–'}</span> },
          ].map(({ label, value }) => (
            <div key={label} className="card p-3">
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              {value}
            </div>
          ))}
        </div>

        {elapsedSeconds !== null && (
          <p className="text-xs text-slate-500 flex items-center justify-center gap-1">
            <Clock size={12} /> Completed in {elapsedSeconds}s
          </p>
        )}

        {runStatus?.error_message && (
          <div className="p-3 rounded-lg bg-red-900/20 border border-red-700/30 text-sm text-red-300 text-left">
            {runStatus.error_message}
          </div>
        )}

        {!runStatus?.status || runStatus.status === 'RUNNING' || runStatus.status === 'PENDING' ? (
          <p className="text-xs text-slate-600 animate-pulse">Polling status every 2 seconds…</p>
        ) : runStatus.status === 'COMPLETED' && kpiData ? (
          <button className="btn-primary" onClick={() => setStep('kpis')}>
            View KPI Results <ChevronRight size={16} />
          </button>
        ) : null}
      </div>
    </div>
  );

  // ── Step: KPIs ────────────────────────────────────────────────────────────
  if (step === 'kpis' && kpiData) return (
    <div className="max-w-5xl mx-auto animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">KPI Measurements</h1>
          <p className="text-sm text-slate-500">Run #{runId} · {runStatus?.agent_name}</p>
        </div>
        <div className="flex gap-2">
          {evaluation && (
            <button className="btn-primary text-xs" onClick={() => setStep('results')}>
              View CARE Score <ChevronRight size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1">
          <CoverageBar coverage={kpiData.coverage} />
        </div>

        <div className="lg:col-span-3">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>KPI</th>
                  <th>Value</th>
                  <th>Unit</th>
                  <th>Source</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {kpiData.measurements.map(m => (
                  <tr key={m.id}>
                    <td className="font-medium text-slate-200 font-mono text-xs">{m.kpi_name}</td>
                    <td>
                      {m.calculation_status === 'calculated' && m.raw_value !== null ? (
                        <span className="text-sm font-bold text-emerald-400">
                          {typeof m.raw_value === 'number' ? m.raw_value.toFixed(2) : m.raw_value}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-600 italic">—</span>
                      )}
                    </td>
                    <td className="text-xs text-slate-500">{m.unit || '—'}</td>
                    <td><SourceBadge source={m.source} status={m.calculation_status} /></td>
                    <td className="text-[11px] text-slate-500 max-w-xs truncate" title={m.notes}>
                      {m.notes || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {evaluation && (
        <button className="btn-primary w-full justify-center" onClick={() => setStep('results')}>
          View Full CARE Score & Recommendations <ChevronRight size={16} />
        </button>
      )}
    </div>
  );

  // ── Step: Results ─────────────────────────────────────────────────────────
  if (step === 'results' && evaluation) return (
    <div className="max-w-5xl mx-auto animate-fade-in space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">{evaluation.agent_name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="px-2 py-0.5 bg-bg-hover rounded text-xs text-slate-400">{evaluation.agent_type}</span>
            <span className="px-2 py-0.5 rounded text-xs bg-indigo-900/30 text-indigo-300 border border-indigo-700/30">
              Automated Run #{runId}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary text-xs" onClick={() => setStep('kpis')}>
            ← KPI Details
          </button>
          <button className="btn-primary text-xs" onClick={() => navigate(`/results/${evaluation.id}`)}>
            Full Report <ExternalLink size={12} />
          </button>
        </div>
      </div>

      {/* Score Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card-glass p-6 flex flex-col items-center">
          <CAREScoreGauge score={evaluation.care_score} size="lg" recommendation={evaluation.recommendation} />
          <p className="text-xs text-slate-500 mt-2 text-center">Generated from automated evaluation</p>
          {kpiData && (
            <div className="mt-3 w-full">
              <CoverageBar coverage={kpiData.coverage} />
            </div>
          )}
        </div>

        <div className="lg:col-span-2 grid grid-cols-2 gap-3 content-start">
          {(['c', 'a', 'r', 'e'] as const).map(dim => (
            <DimensionCard
              key={dim} dimension={dim}
              score={evaluation[`score_${dim}` as keyof Evaluation] as number}
              weight={evaluation[`weight_${dim}` as keyof Evaluation] as number}
            />
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {(evaluation.recommendations?.length ?? 0) > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={18} className="text-amber-400" />
            <p className="text-sm font-semibold text-slate-200">Recommendations</p>
            <span className="badge bg-amber-900/40 text-amber-300 border border-amber-700/30">
              {evaluation.recommendations!.length}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {evaluation.recommendations!.map((rec, i) => (
              <RecommendationCard key={i} recommendation={rec as any} index={i} />
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button className="btn-secondary flex-1 justify-center" onClick={() => { setStep('configure'); setRunId(null); setRunStatus(null); setKpiData(null); setEvaluation(null); }}>
          Run Another Evaluation
        </button>
        <button className="btn-primary flex-1 justify-center" onClick={() => navigate(`/results/${evaluation.id}`)}>
          Open Full Report <ExternalLink size={16} />
        </button>
      </div>
    </div>
  );

  return null;
};

export default AutomatedEvaluation;
