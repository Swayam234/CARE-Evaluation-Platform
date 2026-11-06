/**
 * Comparison Page – Side-by-side agent comparison.
 * – Dual radar chart overlay
 * – Bar chart comparing CARE scores
 * – KPI delta table (highlights winner per KPI)
 * – Overall winner badge
 */
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  GitCompare, Trophy, ArrowLeft, PlusCircle, X, TrendingUp, TrendingDown, Minus,
} from 'lucide-react';
import { toast } from 'react-toastify';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer,
} from 'recharts';
import { clsx } from 'clsx';
import { evaluationsApi, comparisonApi } from '../services/api';
import type { EvaluationSummary, ComparisonResult } from '../types';
import { KPI_DEFINITIONS, DIMENSION_INFO } from '../types';
import CARERadarChart from '../components/RadarChart';
import { formatScore, getRecommendationBadge } from '../utils';
import LoadingSkeleton from '../components/LoadingSkeleton';

const AGENT_COLORS = ['#6366F1', '#10B981', '#F59E0B', '#3B82F6', '#EC4899'];

const Comparison: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [allEvaluations, setAllEvaluations] = useState<EvaluationSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    evaluationsApi.list().then(setAllEvaluations).catch(() => {});
    const idsParam = searchParams.get('ids');
    if (idsParam) {
      const ids = idsParam.split(',').map(Number).filter(Boolean);
      setSelectedIds(ids);
    }
  }, [searchParams]);

  // Auto-compare when IDs are pre-selected from History
  useEffect(() => {
    if (selectedIds.length >= 2) handleCompare();
  }, []);  // eslint-disable-line

  const handleCompare = async () => {
    if (selectedIds.length < 2) {
      toast.warning('Select at least 2 agents to compare');
      return;
    }
    setComparing(true);
    try {
      const data = await comparisonApi.compare(selectedIds);
      setResult(data);
    } catch (e: any) {
      toast.error(e.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const toggleAgent = (id: number) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((i) => i !== id);
      if (prev.length >= 5) { toast.warning('Max 5 agents'); return prev; }
      return [...prev, id];
    });
    setResult(null);
  };

  // Build radar data
  const radarData = result
    ? ['Computational', 'Accuracy', 'Reliability', 'Economics'].map((label, idx) => {
        const dimKey = ['c', 'a', 'r', 'e'][idx];
        const dimComp = result.dimension_comparisons.find(
          (d) => d.dimension.toLowerCase().startsWith(dimKey === 'c' ? 'comp' : dimKey === 'a' ? 'acc' : dimKey === 'r' ? 'rel' : 'eco')
        );
        const row: { dimension: string; [key: string]: string | number } = { dimension: label };
        result.agents.forEach((agent) => {
          row[agent.agent_name] = dimComp?.scores[agent.agent_name] ?? 0;
        });
        return row;
      })
    : [];

  // Bar chart data
  const barData = result
    ? [{
        name: 'CARE Score',
        ...result.agents.reduce((acc, agent) => ({
          ...acc,
          [agent.agent_name]: result.care_score_comparison[agent.agent_name] ?? 0,
        }), {}),
      }]
    : [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <GitCompare size={24} className="text-care-c" />
        <div>
          <h1 className="text-xl font-bold text-slate-100">Agent Comparison</h1>
          <p className="text-xs text-slate-500">Compare up to 5 agents side-by-side</p>
        </div>
      </div>

      {/* Agent selector */}
      <div className="card p-5">
        <p className="text-sm font-semibold text-slate-300 mb-3">
          Select Agents to Compare ({selectedIds.length}/5)
        </p>
        <div className="flex flex-wrap gap-2 mb-4">
          {allEvaluations.map((ev, idx) => {
            const isSelected = selectedIds.includes(ev.id);
            const colorIdx = selectedIds.indexOf(ev.id);
            const color = colorIdx >= 0 ? AGENT_COLORS[colorIdx] : '#475569';
            return (
              <button
                key={ev.id}
                id={`compare-agent-${ev.id}`}
                onClick={() => toggleAgent(ev.id)}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all duration-200',
                  isSelected
                    ? 'border-opacity-50 text-white'
                    : 'border-bg-border text-slate-400 hover:border-slate-500 hover:text-slate-200'
                )}
                style={isSelected ? { borderColor: color, backgroundColor: `${color}20`, color } : {}}
              >
                {isSelected && (
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                )}
                {ev.agent_name}
                <span className="text-[10px] opacity-70">{formatScore(ev.care_score)}</span>
                {isSelected && <X size={10} />}
              </button>
            );
          })}
        </div>
        <button
          id="run-comparison-btn"
          onClick={handleCompare}
          disabled={selectedIds.length < 2 || comparing}
          className="btn-primary"
        >
          <GitCompare size={16} />
          {comparing ? 'Comparing…' : 'Run Comparison'}
        </button>
      </div>

      {/* Loading */}
      {comparing && <LoadingSkeleton />}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Overall winner banner */}
          <div className="card-glass p-5 flex items-center gap-4 border border-amber-500/30">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <Trophy size={24} className="text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-amber-400 font-bold uppercase tracking-widest">Overall Winner</p>
              <p className="text-xl font-black text-slate-100">{result.overall_winner}</p>
              <p className="text-xs text-slate-500">
                CARE Score: {formatScore(result.care_score_comparison[result.overall_winner])}
              </p>
            </div>
            <div className="ml-auto">
              <span className={getRecommendationBadge(
                result.agents.find((a) => a.agent_name === result.overall_winner)?.recommendation
              )}>
                {result.agents.find((a) => a.agent_name === result.overall_winner)?.recommendation ?? 'N/A'}
              </span>
            </div>
          </div>

          {/* Agent summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {result.agents.map((agent, idx) => {
              const color = AGENT_COLORS[idx] ?? '#6366F1';
              const isWinner = agent.agent_name === result.overall_winner;
              return (
                <div
                  key={agent.id}
                  className="card p-4"
                  style={{ borderColor: isWinner ? `${color}60` : `${color}25` }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                      <p className="font-semibold text-slate-100 text-sm">{agent.agent_name}</p>
                    </div>
                    {isWinner && <Trophy size={14} className="text-amber-400" />}
                  </div>
                  <p className="text-3xl font-black mb-1" style={{ color }}>
                    {formatScore(agent.care_score)}
                  </p>
                  <span className={getRecommendationBadge(agent.recommendation)}>
                    {agent.recommendation ?? 'N/A'}
                  </span>
                  <div className="mt-3 grid grid-cols-4 gap-1 text-center">
                    {(['score_c', 'score_a', 'score_r', 'score_e'] as const).map((k, di) => {
                      const dim = (['c', 'a', 'r', 'e'] as const)[di];
                      return (
                        <div key={k} className="text-center">
                          <p className="text-[10px] text-slate-500">{DIMENSION_INFO[dim].short}</p>
                          <p className="text-xs font-bold" style={{ color: DIMENSION_INFO[dim].color }}>
                            {formatScore(agent[k])}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Radar overlay */}
            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-300 mb-4">Dimension Profile (Radar)</p>
              <CARERadarChart
                data={radarData}
                series={result.agents.map((agent, idx) => ({
                  name: agent.agent_name,
                  color: AGENT_COLORS[idx] ?? '#6366F1',
                  dataKey: agent.agent_name,
                }))}
                height={280}
              />
            </div>

            {/* Bar chart */}
            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-300 mb-4">CARE Score Comparison</p>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={result.agents.map((agent, idx) => ({
                    name: agent.agent_name.length > 16 ? agent.agent_name.slice(0, 16) + '…' : agent.agent_name,
                    score: agent.care_score ?? 0,
                    fill: AGENT_COLORS[idx],
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #2D3748', borderRadius: '8px' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {result.agents.map((_, idx) => (
                      <Cell key={idx} fill={AGENT_COLORS[idx] ?? '#6366F1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Dimension winner table */}
          <div className="card p-5">
            <p className="text-sm font-semibold text-slate-300 mb-4">Dimension Winners</p>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Dimension</th>
                    {result.agents.map((agent, idx) => (
                      <th key={agent.id}>
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: AGENT_COLORS[idx] }} />
                          {agent.agent_name}
                        </div>
                      </th>
                    ))}
                    <th>Winner</th>
                  </tr>
                </thead>
                <tbody>
                  {result.dimension_comparisons.map((dc) => (
                    <tr key={dc.dimension}>
                      <td className="font-medium text-slate-200">{dc.dimension}</td>
                      {result.agents.map((agent) => {
                        const score = dc.scores[agent.agent_name] ?? null;
                        const isWinner = agent.agent_name === dc.winner;
                        return (
                          <td key={agent.id} className={clsx(isWinner && 'bg-emerald-900/10')}>
                            <span className={clsx(
                              'font-bold',
                              isWinner ? 'text-emerald-400' : 'text-slate-400'
                            )}>
                              {formatScore(score)}
                            </span>
                          </td>
                        );
                      })}
                      <td>
                        <span className="badge badge-production">{dc.winner}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* KPI Delta Table */}
          <div className="card p-5">
            <p className="text-sm font-semibold text-slate-300 mb-4">KPI Comparison</p>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>KPI</th>
                    <th>Dimension</th>
                    {result.agents.map((agent, idx) => (
                      <th key={agent.id}>
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: AGENT_COLORS[idx] }} />
                          {agent.agent_name.length > 14 ? agent.agent_name.slice(0, 14) + '…' : agent.agent_name}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {KPI_DEFINITIONS.map((kpi) => {
                    const kpiData = result.kpi_comparison[kpi.key];
                    if (!kpiData) return null;
                    const values = result.agents.map((a) => kpiData[a.agent_name] ?? null);
                    if (values.every((v) => v === null)) return null;
                    const validVals = values.filter((v) => v !== null) as number[];
                    const maxVal = Math.max(...validVals);
                    const dimInfo = DIMENSION_INFO[kpi.dimension];
                    return (
                      <tr key={kpi.key}>
                        <td className="text-slate-200 text-xs">{kpi.label}</td>
                        <td>
                          <span
                            className="px-1.5 py-0.5 rounded text-[10px] font-bold"
                            style={{ backgroundColor: `${dimInfo.color}20`, color: dimInfo.color }}
                          >
                            {dimInfo.short}
                          </span>
                        </td>
                        {result.agents.map((agent, idx) => {
                          const val = kpiData[agent.agent_name];
                          const isMax = val === maxVal && val !== null;
                          const isMin = val !== null && val === Math.min(...validVals) && validVals.length > 1;
                          const showWinner = isMax && !kpi.lowerIsBetter || isMin && kpi.lowerIsBetter;
                          return (
                            <td key={agent.id} className={clsx(showWinner && 'bg-emerald-900/10')}>
                              <div className="flex items-center gap-1">
                                <span className={clsx('text-xs font-semibold', showWinner ? 'text-emerald-400' : 'text-slate-400')}>
                                  {val != null ? val.toFixed(2) : '–'}
                                </span>
                                {showWinner && <TrendingUp size={10} className="text-emerald-400" />}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !comparing && (
        <div className="card p-12 text-center">
          <GitCompare size={48} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-300 font-semibold mb-2">Select agents to compare</p>
          <p className="text-slate-500 text-sm">Choose 2–5 agents from the list above</p>
        </div>
      )}
    </div>
  );
};

export default Comparison;
