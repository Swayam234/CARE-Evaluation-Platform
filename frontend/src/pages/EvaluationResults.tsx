/**
 * EvaluationResults Page
 * – CARE Score gauge (animated)
 * – Radar chart
 * – Per-dimension score cards
 * – Strengths / Weaknesses / Recommendations
 * – KPI breakdown table
 * – Export PDF / Export CSV
 */
import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, FileText, Copy, Trash2,
  CheckCircle2, XCircle, AlertTriangle, Info,
} from 'lucide-react';
import { toast } from 'react-toastify';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { evaluationsApi } from '../services/api';
import type { Evaluation } from '../types';
import { KPI_DEFINITIONS, DIMENSION_INFO } from '../types';
import CAREScoreGauge from '../components/CAREScoreGauge';
import DimensionCard from '../components/DimensionCard';
import CARERadarChart from '../components/RadarChart';
import RecommendationCard from '../components/RecommendationCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { formatScore, formatDateTime, getRecommendationBadge } from '../utils';

const EvaluationResults: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ev, setEv] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [exportingPdf, setExportingPdf] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    evaluationsApi.get(Number(id))
      .then(setEv)
      .catch(() => toast.error('Failed to load evaluation'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    if (!ev || !confirm(`Delete evaluation for "${ev.agent_name}"?`)) return;
    try {
      await evaluationsApi.delete(ev.id);
      toast.success('Evaluation deleted');
      navigate('/history');
    } catch {
      toast.error('Failed to delete');
    }
  };

  const handleDuplicate = async () => {
    if (!ev) return;
    try {
      const copy = await evaluationsApi.duplicate(ev.id);
      toast.success(`Duplicated as "${copy.agent_name}"`);
      navigate(`/results/${copy.id}`);
    } catch {
      toast.error('Failed to duplicate');
    }
  };

  const handleExportPdf = async () => {
    if (!reportRef.current || !ev) return;
    setExportingPdf(true);
    try {
      const canvas = await html2canvas(reportRef.current, {
        backgroundColor: '#0A0F1E',
        scale: 2,
        useCORS: true,
      });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let yPos = 0;
      while (yPos < imgHeight) {
        if (yPos > 0) pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, -yPos, imgWidth, imgHeight);
        yPos += pageHeight;
      }
      pdf.save(`CARE_Report_${ev.agent_name.replace(/\s+/g, '_')}.pdf`);
      toast.success('PDF exported!');
    } catch {
      toast.error('PDF export failed');
    } finally {
      setExportingPdf(false);
    }
  };

  const handleExportCsv = () => {
    if (!ev) return;
    const rows = [
      ['Field', 'Value'],
      ['Agent Name', ev.agent_name],
      ['Agent Type', ev.agent_type],
      ['CARE Score', ev.care_score ?? ''],
      ['Recommendation', ev.recommendation ?? ''],
      ['Score C', ev.score_c ?? ''],
      ['Score A', ev.score_a ?? ''],
      ['Score R', ev.score_r ?? ''],
      ['Score E', ev.score_e ?? ''],
      ...KPI_DEFINITIONS.map((k) => [k.label, ev[k.key as keyof Evaluation] ?? '']),
    ];
    const csv = rows.map((r) => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CARE_${ev.agent_name.replace(/\s+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('CSV exported!');
  };

  if (loading) return <LoadingSkeleton type="gauge" />;
  if (!ev) return (
    <div className="card p-12 text-center">
      <p className="text-slate-400">Evaluation not found.</p>
      <button onClick={() => navigate('/history')} className="btn-secondary mt-4">Back to History</button>
    </div>
  );

  const radarData = [
    { dimension: 'Computational', [ev.agent_name]: ev.score_c ?? 0 },
    { dimension: 'Accuracy', [ev.agent_name]: ev.score_a ?? 0 },
    { dimension: 'Reliability', [ev.agent_name]: ev.score_r ?? 0 },
    { dimension: 'Economics', [ev.agent_name]: ev.score_e ?? 0 },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/history')} className="btn-ghost">
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-100">{ev.agent_name}</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="px-2 py-0.5 bg-bg-hover rounded text-xs text-slate-400">{ev.agent_type}</span>
              <span className={getRecommendationBadge(ev.recommendation)}>{ev.recommendation ?? 'N/A'}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleExportPdf} disabled={exportingPdf} className="btn-secondary text-xs">
            <FileText size={14} />
            {exportingPdf ? 'Exporting…' : 'Export PDF'}
          </button>
          <button onClick={handleExportCsv} className="btn-secondary text-xs">
            <Download size={14} />
            Export CSV
          </button>
          <button onClick={handleDuplicate} className="btn-ghost text-xs">
            <Copy size={14} />
            Duplicate
          </button>
          <button onClick={handleDelete} className="btn-danger text-xs">
            <Trash2 size={14} />
            Delete
          </button>
        </div>
      </div>

      <div ref={reportRef} className="space-y-6">
        {/* Score overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Gauge */}
          <div className="card-glass p-6 flex flex-col items-center justify-center">
            <CAREScoreGauge
              score={ev.care_score ?? undefined}
              size="lg"
              recommendation={ev.recommendation}
            />
            <div className="mt-2 text-center text-xs text-slate-500">
              Evaluated {formatDateTime(ev.created_at)}
              {ev.evaluator && ` · by ${ev.evaluator}`}
            </div>
          </div>

          {/* Radar Chart */}
          <div className="card p-5 flex flex-col">
            <p className="text-sm font-semibold text-slate-300 mb-3">Dimension Profile</p>
            <div className="flex-1">
              <CARERadarChart
                data={radarData}
                series={[{ name: ev.agent_name, color: '#6366F1', dataKey: ev.agent_name }]}
                height={220}
              />
            </div>
          </div>

          {/* Weights used */}
          <div className="card p-5">
            <p className="text-sm font-semibold text-slate-300 mb-3">Weights Used</p>
            <div className="space-y-3">
              {(['c', 'a', 'r', 'e'] as const).map((dim) => {
                const wKey = `weight_${dim}` as keyof Evaluation;
                const w = (ev[wKey] as number) * 100;
                return (
                  <div key={dim}>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: DIMENSION_INFO[dim].color }}>{DIMENSION_INFO[dim].label}</span>
                      <span className="text-slate-400">{w.toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${w}%`, backgroundColor: DIMENSION_INFO[dim].color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Dimension score cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {(['c', 'a', 'r', 'e'] as const).map((dim) => (
            <DimensionCard
              key={dim}
              dimension={dim}
              score={ev[`score_${dim}` as keyof Evaluation] as number}
              weight={ev[`weight_${dim}` as keyof Evaluation] as number}
            />
          ))}
        </div>

        {/* Strengths & Weaknesses */}
        {((ev.strengths?.length ?? 0) > 0 || (ev.weaknesses?.length ?? 0) > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(ev.strengths?.length ?? 0) > 0 && (
              <div className="card p-5">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 size={18} className="text-emerald-400" />
                  <p className="text-sm font-semibold text-emerald-400">Strengths</p>
                </div>
                <ul className="space-y-2">
                  {ev.strengths!.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className="text-emerald-500 mt-0.5">✓</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(ev.weaknesses?.length ?? 0) > 0 && (
              <div className="card p-5">
                <div className="flex items-center gap-2 mb-3">
                  <XCircle size={18} className="text-red-400" />
                  <p className="text-sm font-semibold text-red-400">Weaknesses</p>
                </div>
                <ul className="space-y-2">
                  {ev.weaknesses!.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className="text-red-500 mt-0.5">✗</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Recommendations */}
        {(ev.recommendations?.length ?? 0) > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={18} className="text-amber-400" />
              <p className="text-sm font-semibold text-slate-200">Recommendations</p>
              <span className="badge bg-amber-900/40 text-amber-300 border border-amber-700/30">
                {ev.recommendations!.length}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {ev.recommendations!.map((rec, i) => (
                <RecommendationCard key={i} recommendation={rec as any} index={i} />
              ))}
            </div>
          </div>
        )}

        {/* KPI Breakdown Table */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Info size={18} className="text-care-c" />
            <p className="text-sm font-semibold text-slate-200">KPI Breakdown</p>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>KPI</th>
                  <th>Dimension</th>
                  <th>Raw Value</th>
                  <th>Unit</th>
                  <th>Normalized Score</th>
                </tr>
              </thead>
              <tbody>
                {KPI_DEFINITIONS.map((kpi) => {
                  const raw = ev[kpi.key as keyof Evaluation] as number | undefined;
                  const normalized = ev.kpi_scores?.[kpi.key];
                  if (raw == null && normalized == null) return null;
                  const dimInfo = DIMENSION_INFO[kpi.dimension];
                  return (
                    <tr key={kpi.key}>
                      <td className="font-medium text-slate-200">
                        {kpi.label}
                        {kpi.lowerIsBetter && (
                          <span className="ml-1 text-[10px] text-amber-400">(↓ lower is better)</span>
                        )}
                      </td>
                      <td>
                        <span
                          className="px-2 py-0.5 rounded text-xs font-semibold"
                          style={{ backgroundColor: `${dimInfo.color}20`, color: dimInfo.color }}
                        >
                          {dimInfo.short}
                        </span>
                      </td>
                      <td className="text-slate-300">{raw != null ? raw.toFixed(2) : '–'}</td>
                      <td className="text-slate-500 text-xs">{kpi.unit}</td>
                      <td>
                        {normalized != null ? (
                          <div className="flex items-center gap-2">
                            <div className="progress-bar w-20">
                              <div
                                className="progress-fill"
                                style={{ width: `${normalized}%`, backgroundColor: dimInfo.color }}
                              />
                            </div>
                            <span className="text-sm font-semibold" style={{ color: dimInfo.color }}>
                              {normalized.toFixed(1)}
                            </span>
                          </div>
                        ) : <span className="text-slate-600">–</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationResults;
