/**
 * Analytics Page
 * – Line chart: CARE score trend over time
 * – Bar chart: dimension average scores
 * – Pie chart: KPI weight breakdown
 * – Histogram: score distribution
 */
import React, { useEffect, useState } from 'react';
import { TrendingUp, BarChart3, PieChart, RefreshCw } from 'lucide-react';
import { toast } from 'react-toastify';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart as RPieChart, Pie, Cell, Sector,
} from 'recharts';
import { analyticsApi } from '../services/api';
import type { AnalyticsSummary } from '../types';
import { DIMENSION_INFO } from '../types';
import DimensionCard from '../components/DimensionCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { formatScore } from '../utils';

const SCORE_COLORS = {
  'Excellent (90-100)': '#10B981',
  'Good (80-89)': '#3B82F6',
  'Fair (70-79)': '#F59E0B',
  'Poor (<70)': '#EF4444',
};

const CustomTooltipStyle = {
  contentStyle: { backgroundColor: '#1E293B', border: '1px solid #2D3748', borderRadius: '8px' },
  labelStyle: { color: '#e2e8f0', fontWeight: 600 },
  itemStyle: { color: '#94a3b8' },
};

const Analytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activePieIdx, setActivePieIdx] = useState<number | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    try {
      setAnalytics(await analyticsApi.getSummary());
    } catch {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <LoadingSkeleton />;
  if (!analytics) return null;

  // Trend line chart data
  const trendData = analytics.trend.map((pt) => ({
    date: new Date(pt.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    CARE: pt.care_score,
    C: pt.score_c,
    A: pt.score_a,
    R: pt.score_r,
    E: pt.score_e,
    agent: pt.agent_name,
  }));

  // Dimension bar chart data
  const dimBarData = [
    { name: 'Comp. Intelligence', score: analytics.avg_score_c, color: DIMENSION_INFO.c.color },
    { name: 'Accuracy', score: analytics.avg_score_a, color: DIMENSION_INFO.a.color },
    { name: 'Reliability', score: analytics.avg_score_r, color: DIMENSION_INFO.r.color },
    { name: 'Economics', score: analytics.avg_score_e, color: DIMENSION_INFO.e.color },
  ];

  // Score distribution histogram data
  const distData = Object.entries(analytics.score_distribution).map(([bucket, count]) => ({
    bucket,
    count,
    color: SCORE_COLORS[bucket as keyof typeof SCORE_COLORS] ?? '#6366F1',
  }));

  // Pie chart: dimension weight breakdown (using default weights as illustration)
  const pieData = [
    { name: 'Computational (C)', value: 25, color: DIMENSION_INFO.c.color },
    { name: 'Accuracy (A)', value: 30, color: DIMENSION_INFO.a.color },
    { name: 'Reliability (R)', value: 30, color: DIMENSION_INFO.r.color },
    { name: 'Economics (E)', value: 15, color: DIMENSION_INFO.e.color },
  ];

  const renderActiveShape = (props: any) => {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
    return (
      <g>
        <text x={cx} y={cy - 10} textAnchor="middle" fill="#e2e8f0" style={{ fontSize: 13, fontWeight: 700 }}>
          {payload.name.split(' ')[0]}
        </text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill={fill} style={{ fontSize: 18, fontWeight: 900 }}>
          {value}%
        </text>
        <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 8} startAngle={startAngle} endAngle={endAngle} fill={fill} />
        <Sector cx={cx} cy={cy} innerRadius={outerRadius + 12} outerRadius={outerRadius + 16} startAngle={startAngle} endAngle={endAngle} fill={fill} />
      </g>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 size={24} className="text-care-c" />
          <div>
            <h1 className="text-xl font-bold text-slate-100">Analytics</h1>
            <p className="text-xs text-slate-500">{analytics.total_evaluations} total evaluations</p>
          </div>
        </div>
        <button onClick={load} className="btn-ghost text-xs">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* KPI summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {(['c', 'a', 'r', 'e'] as const).map((dim) => (
          <DimensionCard
            key={dim}
            dimension={dim}
            score={analytics[`avg_score_${dim}` as keyof AnalyticsSummary] as number}
          />
        ))}
      </div>

      {/* CARE Score Trend Line Chart */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={16} className="text-care-c" />
          <p className="text-sm font-semibold text-slate-200">CARE Score Trend Over Time</p>
        </div>
        {trendData.length < 2 ? (
          <p className="text-slate-500 text-sm text-center py-8">Need at least 2 evaluations to show trend.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
              <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip {...CustomTooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
              <Line type="monotone" dataKey="CARE" stroke="#8B5CF6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="C" stroke={DIMENSION_INFO.c.color} strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
              <Line type="monotone" dataKey="A" stroke={DIMENSION_INFO.a.color} strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
              <Line type="monotone" dataKey="R" stroke={DIMENSION_INFO.r.color} strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
              <Line type="monotone" dataKey="E" stroke={DIMENSION_INFO.e.color} strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Bottom charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dimension averages bar */}
        <div className="card p-5">
          <p className="text-sm font-semibold text-slate-200 mb-4">Avg Dimension Scores</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={dimBarData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} width={110} />
              <Tooltip
                {...CustomTooltipStyle}
                formatter={(v: number) => [v.toFixed(1), 'Avg Score']}
              />
              <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                {dimBarData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Score distribution histogram */}
        <div className="card p-5">
          <p className="text-sm font-semibold text-slate-200 mb-4">Score Distribution</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={distData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
              <XAxis dataKey="bucket" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip {...CustomTooltipStyle} formatter={(v: number) => [v, 'Count']} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {distData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie chart: weight breakdown */}
        <div className="card p-5">
          <p className="text-sm font-semibold text-slate-200 mb-4">Default Weight Breakdown</p>
          <RPieChart width={220} height={220} style={{ margin: '0 auto' }}>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              dataKey="value"
              activeIndex={activePieIdx}
              activeShape={renderActiveShape}
              onMouseEnter={(_, index) => setActivePieIdx(index)}
              onMouseLeave={() => setActivePieIdx(undefined)}
            >
              {pieData.map((entry, index) => (
                <Cell key={index} fill={entry.color} strokeWidth={0} />
              ))}
            </Pie>
          </RPieChart>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 justify-center">
            {pieData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-[10px] text-slate-400">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                {entry.name}: {entry.value}%
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Agents */}
      {analytics.top_agents.length > 0 && (
        <div className="card p-5">
          <p className="text-sm font-semibold text-slate-200 mb-4">🏆 Top Performing Agents</p>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Agent</th>
                  <th>Type</th>
                  <th>CARE Score</th>
                  <th>C</th>
                  <th>A</th>
                  <th>R</th>
                  <th>E</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {analytics.top_agents.map((agent, idx) => (
                  <tr key={agent.id}>
                    <td>
                      <span className={`font-black ${idx === 0 ? 'text-amber-400' : idx === 1 ? 'text-slate-300' : 'text-amber-700'}`}>
                        #{idx + 1}
                      </span>
                    </td>
                    <td className="font-semibold text-slate-100">{agent.agent_name}</td>
                    <td className="text-slate-400 text-xs">{agent.agent_type}</td>
                    <td className="font-black text-purple-400">{formatScore(agent.care_score)}</td>
                    {(['score_c', 'score_a', 'score_r', 'score_e'] as const).map((k, di) => (
                      <td key={k} className="text-sm" style={{ color: DIMENSION_INFO[(['c', 'a', 'r', 'e'] as const)[di]].color }}>
                        {formatScore(agent[k])}
                      </td>
                    ))}
                    <td>
                      <span className={`badge ${
                        agent.recommendation === 'Production Ready' ? 'badge-production' :
                        agent.recommendation === 'Pilot and Scale' ? 'badge-pilot' :
                        agent.recommendation === 'Needs Improvement' ? 'badge-improve' : 'badge-not-recommended'
                      }`}>
                        {agent.recommendation ?? 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
