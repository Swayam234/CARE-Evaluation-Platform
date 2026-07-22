/**
 * Dashboard Page
 * – CARE Score summary card (gauge)
 * – 4 dimension score cards
 * – Deployment recommendation badge
 * – Recent evaluations table
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, TrendingUp, Award, Users, Activity, ArrowRight, RefreshCw, Database } from 'lucide-react';
import { toast } from 'react-toastify';
import { evaluationsApi, analyticsApi, utilsApi } from '../services/api';
import type { EvaluationSummary, AnalyticsSummary } from '../types';
import { DIMENSION_INFO } from '../types';
import CAREScoreGauge from '../components/CAREScoreGauge';
import DimensionCard from '../components/DimensionCard';
import { formatScore, formatDate, getRecommendationBadge, getScoreColor } from '../utils';
import LoadingSkeleton from '../components/LoadingSkeleton';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [recent, setRecent] = useState<EvaluationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [analyticsData, recentData] = await Promise.all([
        analyticsApi.getSummary(),
        evaluationsApi.list({ sort_by: 'created_at', sort_order: 'desc', limit: 5 }),
      ]);
      setAnalytics(analyticsData);
      setRecent(recentData);
    } catch (e: any) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await utilsApi.seed();
      toast.success(res.message || 'Sample data seeded!');
      await loadData();
    } catch {
      toast.error('Seeding failed');
    } finally {
      setSeeding(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const stats = [
    {
      icon: <Users size={20} />,
      label: 'Total Evaluations',
      value: analytics?.total_evaluations ?? 0,
      color: '#6366F1',
    },
    {
      icon: <Award size={20} />,
      label: 'Avg CARE Score',
      value: analytics ? formatScore(analytics.avg_care_score) : '–',
      color: '#8B5CF6',
    },
    {
      icon: <TrendingUp size={20} />,
      label: 'Production Ready',
      value: analytics?.production_ready_count ?? 0,
      color: '#10B981',
    },
    {
      icon: <Activity size={20} />,
      label: 'Needs Improvement',
      value: analytics?.not_recommended_count ?? 0,
      color: '#EF4444',
    },
  ];

  if (loading) return <LoadingSkeleton type="dashboard" />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CARE Score Gauge */}
        <div className="card-glass p-6 flex flex-col items-center justify-center gap-2">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Platform Average</p>
          <CAREScoreGauge
            score={analytics?.avg_care_score}
            size="lg"
            showLabel={false}
          />
          <div className="text-center mt-2">
            <p className="text-sm font-bold text-slate-200">Avg CARE Score</p>
            <p className="text-xs text-slate-500">{analytics?.total_evaluations ?? 0} evaluations</p>
          </div>
        </div>

        {/* Stats cards */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4 content-start">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="card p-5 flex items-center gap-4 hover:-translate-y-0.5 transition-all duration-200"
              style={{ borderColor: `${stat.color}30` }}
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: `${stat.color}20`, color: stat.color }}
              >
                {stat.icon}
              </div>
              <div>
                <p className="text-2xl font-black text-slate-100">{stat.value}</p>
                <p className="text-xs text-slate-500">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dimension Score Cards */}
      <div>
        <div className="section-header">
          <h2 className="section-title">Dimension Averages</h2>
          <span className="text-xs text-slate-500">Across all evaluations</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {(['c', 'a', 'r', 'e'] as const).map((dim) => {
            const scoreKey = `avg_score_${dim}` as keyof AnalyticsSummary;
            return (
              <DimensionCard
                key={dim}
                dimension={dim}
                score={analytics ? (analytics[scoreKey] as number) : undefined}
              />
            );
          })}
        </div>
      </div>

      {/* Recent Evaluations */}
      <div>
        <div className="section-header justify-between">
          <div className="flex items-center gap-3">
            <h2 className="section-title">Recent Evaluations</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="btn-ghost text-xs"
              title="Seed sample data"
            >
              <Database size={14} />
              {seeding ? 'Seeding…' : 'Seed Sample Data'}
            </button>
            <button
              onClick={loadData}
              className="btn-ghost text-xs"
            >
              <RefreshCw size={14} />
              Refresh
            </button>
            <button
              onClick={() => navigate('/history')}
              className="btn-ghost text-xs"
            >
              View All
              <ArrowRight size={14} />
            </button>
          </div>
        </div>

        {recent.length === 0 ? (
          <div className="card p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-care-c/10 flex items-center justify-center mx-auto mb-4">
              <Activity size={28} className="text-care-c" />
            </div>
            <p className="text-slate-300 font-semibold mb-2">No evaluations yet</p>
            <p className="text-slate-500 text-sm mb-6">
              Get started by creating your first evaluation or loading sample data.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button onClick={() => navigate('/evaluate')} className="btn-primary">
                <PlusCircle size={16} />
                New Evaluation
              </button>
              <button onClick={handleSeed} disabled={seeding} className="btn-secondary">
                <Database size={16} />
                Load Sample Data
              </button>
            </div>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Type</th>
                  <th>CARE Score</th>
                  <th className="hidden md:table-cell">C</th>
                  <th className="hidden md:table-cell">A</th>
                  <th className="hidden md:table-cell">R</th>
                  <th className="hidden md:table-cell">E</th>
                  <th>Recommendation</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recent.map((ev) => (
                  <tr
                    key={ev.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/results/${ev.id}`)}
                  >
                    <td className="font-medium text-slate-100">{ev.agent_name}</td>
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
                      <ArrowRight size={14} className="text-slate-600" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="flex gap-3 flex-wrap">
        <button onClick={() => navigate('/evaluate')} className="btn-primary">
          <PlusCircle size={16} />
          New Evaluation
        </button>
        <button onClick={() => navigate('/comparison')} className="btn-secondary">
          Compare Agents
        </button>
        <button onClick={() => navigate('/analytics')} className="btn-secondary">
          View Analytics
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
