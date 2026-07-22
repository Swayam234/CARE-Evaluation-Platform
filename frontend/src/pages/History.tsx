/**
 * History Page – Searchable, filterable, sortable table of all evaluations.
 * Row actions: View, Duplicate, Delete, Compare.
 * Bulk select for comparison.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, SortAsc, SortDesc, Eye, Copy, Trash2,
  GitCompare, Filter, PlusCircle, X,
} from 'lucide-react';
import { toast } from 'react-toastify';
import { clsx } from 'clsx';
import { evaluationsApi } from '../services/api';
import type { EvaluationSummary } from '../types';
import { formatScore, formatDate, getRecommendationBadge, getScoreColor } from '../utils';
import LoadingSkeleton from '../components/LoadingSkeleton';

type SortField = 'created_at' | 'care_score' | 'agent_name';
type SortOrder = 'asc' | 'desc';

const RECOMMENDATION_OPTIONS = [
  'Production Ready', 'Pilot and Scale', 'Needs Improvement', 'Not Recommended',
];

const History: React.FC = () => {
  const navigate = useNavigate();
  const [evaluations, setEvaluations] = useState<EvaluationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [agentType, setAgentType] = useState('');
  const [recommendation, setRecommendation] = useState('');
  const [sortBy, setSortBy] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await evaluationsApi.list({
        search: search || undefined,
        agent_type: agentType || undefined,
        recommendation: recommendation || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setEvaluations(data);
    } catch {
      toast.error('Failed to load evaluations');
    } finally {
      setLoading(false);
    }
  }, [search, agentType, recommendation, sortBy, sortOrder]);

  useEffect(() => { load(); }, [load]);

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleDelete = async (ev: EvaluationSummary) => {
    if (!confirm(`Delete "${ev.agent_name}"?`)) return;
    try {
      await evaluationsApi.delete(ev.id);
      toast.success('Deleted');
      load();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const handleDuplicate = async (ev: EvaluationSummary) => {
    try {
      const copy = await evaluationsApi.duplicate(ev.id);
      toast.success(`Duplicated as "${copy.agent_name}"`);
      load();
    } catch {
      toast.error('Failed to duplicate');
    }
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleCompare = () => {
    const ids = Array.from(selected).join(',');
    navigate(`/comparison?ids=${ids}`);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortBy !== field) return <SortAsc size={12} className="opacity-30" />;
    return sortOrder === 'asc' ? <SortAsc size={12} className="text-care-c" /> : <SortDesc size={12} className="text-care-c" />;
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            id="history-search"
            type="text"
            placeholder="Search agents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-9 text-sm"
          />
        </div>

        {/* Filter toggle */}
        <button
          id="history-filter-toggle"
          onClick={() => setShowFilters((v) => !v)}
          className={clsx('btn-secondary text-sm', showFilters && 'bg-care-c/20 border-care-c/30 text-care-c')}
        >
          <Filter size={14} />
          Filters
          {(agentType || recommendation) && (
            <span className="w-4 h-4 rounded-full bg-care-c text-white text-[9px] flex items-center justify-center">!</span>
          )}
        </button>

        {/* Compare button (when selected) */}
        {selected.size >= 2 && (
          <button
            id="history-compare-btn"
            onClick={handleCompare}
            className="btn-primary text-sm"
          >
            <GitCompare size={14} />
            Compare {selected.size} Agents
          </button>
        )}
        {selected.size > 0 && (
          <button onClick={() => setSelected(new Set())} className="btn-ghost text-xs">
            <X size={12} />
            Clear
          </button>
        )}

        <button onClick={() => navigate('/evaluate')} className="btn-primary ml-auto text-sm">
          <PlusCircle size={14} />
          New Evaluation
        </button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card p-4 flex flex-wrap gap-4 animate-slide-up">
          <div className="flex-1 min-w-[150px]">
            <label className="label text-xs">Agent Type</label>
            <input
              id="filter-agent-type"
              type="text"
              placeholder="e.g. Chatbot"
              value={agentType}
              onChange={(e) => setAgentType(e.target.value)}
              className="input text-sm"
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="label text-xs">Recommendation</label>
            <select
              id="filter-recommendation"
              value={recommendation}
              onChange={(e) => setRecommendation(e.target.value)}
              className="input text-sm"
            >
              <option value="">All</option>
              {RECOMMENDATION_OPTIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => { setAgentType(''); setRecommendation(''); }}
            className="btn-ghost text-xs self-end"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Results count */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span>{evaluations.length} evaluation{evaluations.length !== 1 ? 's' : ''}</span>
        {selected.size > 0 && (
          <span className="text-care-c">· {selected.size} selected</span>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <LoadingSkeleton type="table" />
      ) : evaluations.length === 0 ? (
        <div className="card p-12 text-center">
          <p className="text-slate-400">No evaluations found.</p>
          <button onClick={() => navigate('/evaluate')} className="btn-primary mt-4">
            <PlusCircle size={16} />
            Create First Evaluation
          </button>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th className="w-8">
                  <input
                    type="checkbox"
                    className="rounded border-bg-border bg-bg-secondary"
                    checked={selected.size === evaluations.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelected(new Set(evaluations.map((ev) => ev.id)));
                      } else {
                        setSelected(new Set());
                      }
                    }}
                  />
                </th>
                <th
                  className="cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('agent_name')}
                >
                  <div className="flex items-center gap-1">
                    Agent <SortIcon field="agent_name" />
                  </div>
                </th>
                <th>Type</th>
                <th
                  className="cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('care_score')}
                >
                  <div className="flex items-center gap-1">
                    CARE Score <SortIcon field="care_score" />
                  </div>
                </th>
                <th className="hidden md:table-cell">C</th>
                <th className="hidden md:table-cell">A</th>
                <th className="hidden md:table-cell">R</th>
                <th className="hidden md:table-cell">E</th>
                <th>Recommendation</th>
                <th
                  className="cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('created_at')}
                >
                  <div className="flex items-center gap-1">
                    Date <SortIcon field="created_at" />
                  </div>
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.map((ev) => (
                <tr
                  key={ev.id}
                  className={clsx(selected.has(ev.id) && 'bg-care-c/5')}
                >
                  <td>
                    <input
                      type="checkbox"
                      className="rounded border-bg-border bg-bg-secondary"
                      checked={selected.has(ev.id)}
                      onChange={() => toggleSelect(ev.id)}
                    />
                  </td>
                  <td
                    className="font-medium text-slate-100 cursor-pointer hover:text-care-c transition-colors"
                    onClick={() => navigate(`/results/${ev.id}`)}
                  >
                    {ev.agent_name}
                  </td>
                  <td>
                    <span className="px-2 py-0.5 bg-bg-hover rounded text-xs text-slate-400">
                      {ev.agent_type}
                    </span>
                  </td>
                  <td>
                    <span className={`font-black text-base ${getScoreColor(ev.care_score)}`}>
                      {formatScore(ev.care_score)}
                    </span>
                  </td>
                  {(['score_c', 'score_a', 'score_r', 'score_e'] as const).map((k) => (
                    <td key={k} className={`hidden md:table-cell text-sm ${getScoreColor(ev[k])}`}>
                      {formatScore(ev[k])}
                    </td>
                  ))}
                  <td>
                    <span className={getRecommendationBadge(ev.recommendation)}>
                      {ev.recommendation ?? 'N/A'}
                    </span>
                  </td>
                  <td className="text-slate-500 text-xs">{formatDate(ev.created_at)}</td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button
                        id={`view-btn-${ev.id}`}
                        onClick={() => navigate(`/results/${ev.id}`)}
                        className="p-1.5 rounded hover:bg-care-c/20 text-slate-400 hover:text-care-c transition-colors"
                        title="View"
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        id={`duplicate-btn-${ev.id}`}
                        onClick={() => handleDuplicate(ev)}
                        className="p-1.5 rounded hover:bg-bg-hover text-slate-400 hover:text-slate-200 transition-colors"
                        title="Duplicate"
                      >
                        <Copy size={14} />
                      </button>
                      <button
                        id={`compare-select-btn-${ev.id}`}
                        onClick={() => toggleSelect(ev.id)}
                        className={clsx(
                          'p-1.5 rounded transition-colors',
                          selected.has(ev.id)
                            ? 'text-care-c bg-care-c/20'
                            : 'text-slate-400 hover:text-care-c hover:bg-care-c/10'
                        )}
                        title="Select for comparison"
                      >
                        <GitCompare size={14} />
                      </button>
                      <button
                        id={`delete-btn-${ev.id}`}
                        onClick={() => handleDelete(ev)}
                        className="p-1.5 rounded hover:bg-red-900/30 text-slate-400 hover:text-red-400 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default History;
