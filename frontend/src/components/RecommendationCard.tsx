/**
 * RecommendationCard – Actionable recommendation with icon, severity badge, description.
 */
import React from 'react';
import { clsx } from 'clsx';
import { AlertTriangle, AlertCircle, Info, Minus, Brain, Target, Shield, DollarSign } from 'lucide-react';
import type { Recommendation, DimensionKey } from '../types';
import { DIMENSION_INFO } from '../types';

interface RecommendationCardProps {
  recommendation: Recommendation;
  index?: number;
}

const SEVERITY_CONFIG = {
  critical: {
    badge: 'badge-critical',
    icon: <AlertCircle size={14} />,
    borderColor: '#DC2626',
    bgColor: '#7F1D1D20',
    label: 'Critical',
  },
  high: {
    badge: 'badge-high',
    icon: <AlertTriangle size={14} />,
    borderColor: '#EA580C',
    bgColor: '#7C2D1220',
    label: 'High',
  },
  medium: {
    badge: 'badge-medium',
    icon: <Info size={14} />,
    borderColor: '#D97706',
    bgColor: '#78350F20',
    label: 'Medium',
  },
  low: {
    badge: 'badge-low',
    icon: <Minus size={14} />,
    borderColor: '#475569',
    bgColor: '#1E293B40',
    label: 'Low',
  },
};

const DIMENSION_ICONS: Record<DimensionKey, React.ReactNode> = {
  c: <Brain size={16} />,
  a: <Target size={16} />,
  r: <Shield size={16} />,
  e: <DollarSign size={16} />,
};

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation, index }) => {
  const sevConfig = SEVERITY_CONFIG[recommendation.severity];
  const dimInfo = DIMENSION_INFO[recommendation.dimension];

  return (
    <div
      className="rounded-xl p-4 border transition-all duration-200 hover:-translate-y-0.5 animate-slide-up"
      style={{
        borderColor: sevConfig.borderColor + '50',
        backgroundColor: sevConfig.bgColor,
        animationDelay: `${(index ?? 0) * 60}ms`,
      }}
    >
      <div className="flex items-start gap-3">
        {/* Dimension icon */}
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
          style={{ backgroundColor: `${dimInfo.color}20`, color: dimInfo.color }}
        >
          {DIMENSION_ICONS[recommendation.dimension]}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={clsx('badge', sevConfig.badge)}>
              {sevConfig.icon}
              <span className="ml-1">{sevConfig.label}</span>
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: `${dimInfo.color}20`, color: dimInfo.color }}
            >
              {dimInfo.short} – {dimInfo.label}
            </span>
          </div>
          <p className="text-sm font-semibold text-slate-100">{recommendation.title}</p>
          <p className="text-xs text-slate-400 mt-0.5">{recommendation.description}</p>
        </div>
      </div>
    </div>
  );
};

export default RecommendationCard;
