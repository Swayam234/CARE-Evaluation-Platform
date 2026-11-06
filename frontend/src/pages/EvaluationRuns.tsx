/**
 * EvaluationRuns Page
 * Lists all automated evaluation runs, including their status and links
 * to the generated CARE evaluation results.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot, Plus, RefreshCw, ChevronRight, CheckCircle2, XCircle,
  Clock, Loader2, AlertTriangle, ExternalLink, Trash2,
} from 'lucide-react';
import { clsx } from 'clsx';
import { toast } from 'react-toastify';
import { pipelineApi } from '../services/pipelineApi';
import type { EvaluationRunSummary } from '../types/pipeline';

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'COMPLETED': return <CheckCircle2 size={16} className="text-emerald-400" />;
    case 'FAILED':    return <XCircle size={16} className="text-red-400" />;
    case 'RUNNING':   return <Loader2 size={16} className="text-indigo-400 animate-spin" />;
    default:          return <Clock size={16} className="text-slate-500" />;
  }
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, string> = {
    PENDING:   'bg-slate-800 text-slate-400 border-slate-700',
    RUNNING:   'bg-indigo-900/30 text-indigo-300 border-indigo-700/30',
    COMPLETED: 'bg-emerald-900/30 text-emerald-300 border-emerald-700/30',
    FAILED:    'bg-red-900/30 text-red-300 border-red-700/30',
  };
  return (
    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-bold border', map[status] || map.PENDING)}>
      {status}
    </span>
  );
};

const EvaluationRuns: React.FC = () => {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<EvaluationRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await pipelineApi.listRuns(statusFilter || undefined);
      setRuns(data);
    } catch (e: any) {
      toast.error(e.message || 'Failed to load evaluation runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRuns(); }, [statusFilter]);

  const handleDelete = async (runId: number) => {
    if (!confirm(`Delete evaluation run #${runId}? This cannot be undone.`)) return;
    setDeletingId(runId);
    try {
      await pipelineApi.deleteRun(runId);
      setRuns(prev => prev.filter(r => r.id !== runId));
      toast.success('Evaluation run deleted');
    } catch (e: any) {
      toast.error(e.message || 'Failed to delete run');
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (d?: string) => d ? new Date(d).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }) : '—';

  const calcDuration = (run: EvaluationRunSummary) => {
    if (!run.started_at || !run.completed_at) return null;
    const s = Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000);
    return s < 60 ? `${s}s` : `${Math.round(s / 60)}m ${s % 60}s`;
  };

  return (
    <div className="max-w-6xl mx-auto animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Evaluation Runs</h1>
          <p className="text-sm text-slate-500">All automated evaluation pipeline runs</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input text-sm w-36" value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="RUNNING">Running</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
          </select>
          <button className="btn-ghost text-xs" onClick={fetchRuns} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <button className="btn-primary text-sm" onClick={() => navigate('/automated-evaluation')}>
            <Plus size={14} /> New Run
          </button>
        </div>
      </div>

      {/* Runs Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 size={32} className="animate-spin text-indigo-400" />
        </div>
      ) : runs.length === 0 ? (
        <div className="card p-12 text-center space-y-4">
          <Bot size={48} className="mx-auto text-slate-600" />
          <div>
            <p className="text-slate-400 font-medium">No evaluation runs yet</p>
            <p className="text-slate-600 text-sm">Start an automated evaluation to generate runs</p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/automated-evaluation')}>
            <Plus size={16} /> Start Evaluation
          </button>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Agent</th>
                <th>Status</th>
                <th>Tasks</th>
                <th>Duration</th>
                <th>Created</th>
                <th>CARE Evaluation</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => (
                <tr
                  key={run.id}
                  className="group cursor-pointer hover:bg-bg-hover/50 transition-colors"
                  onClick={() => {
                    if (run.evaluation_id) {
                      navigate(`/results/${run.evaluation_id}`);
                    } else {
                      navigate('/automated-evaluation');
                    }
                  }}
                >
                  <td className="font-mono text-slate-500 text-xs">#{run.id}</td>
                  <td>
                    <div>
                      <p className="font-medium text-slate-200">{run.agent_name}</p>
                      <p className="text-xs text-slate-500">{run.agent_type}</p>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <StatusIcon status={run.status} />
                      <StatusBadge status={run.status} />
                    </div>
                  </td>
                  <td className="text-slate-300">{run.total_tasks ?? '—'}</td>
                  <td className="text-slate-400 text-xs">{calcDuration(run) || '—'}</td>
                  <td className="text-slate-500 text-xs">{formatDate(run.created_at)}</td>
                  <td onClick={e => e.stopPropagation()}>
                    {run.evaluation_id ? (
                      <button className="btn-ghost text-xs text-indigo-400 hover:text-indigo-300"
                        onClick={() => navigate(`/results/${run.evaluation_id}`)}>
                        View #{run.evaluation_id} <ExternalLink size={12} />
                      </button>
                    ) : (
                      <span className="text-xs text-slate-600 italic">
                        {run.status === 'COMPLETED' ? 'Not generated' : '—'}
                      </span>
                    )}
                  </td>
                  <td onClick={e => e.stopPropagation()}>
                    <button className="btn-ghost text-red-400/60 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => handleDelete(run.id)} disabled={deletingId === run.id}>
                      {deletingId === run.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary */}
      {runs.length > 0 && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Total', value: runs.length, cls: '' },
            { label: 'Completed', value: runs.filter(r => r.status === 'COMPLETED').length, cls: 'text-emerald-400' },
            { label: 'Running', value: runs.filter(r => r.status === 'RUNNING').length, cls: 'text-indigo-400' },
            { label: 'Failed', value: runs.filter(r => r.status === 'FAILED').length, cls: 'text-red-400' },
          ].map(({ label, value, cls }) => (
            <div key={label} className="card p-4 text-center">
              <p className={clsx('text-2xl font-black', cls || 'text-slate-200')}>{value}</p>
              <p className="text-xs text-slate-500 mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EvaluationRuns;
