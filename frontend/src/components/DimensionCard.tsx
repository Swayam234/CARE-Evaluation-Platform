/**
 * DimensionCard – shows a CARE dimension letter, score, color, and mini progress bar.
 */
import React from 'react';
import { clsx } from 'clsx';
import { DIMENSION_INFO } from '../types';
import type { DimensionKey } from '../types';
import { formatScore } from '../utils';

interface DimensionCardProps {
  dimension: DimensionKey;
  score?: number | null;
  weight?: number;
  className?: string;
  size?: 'sm' | 'md';
}

const DimensionCard: React.FC<DimensionCardProps> = ({
  dimension,
  score,
  weight,
  className,
  size = 'md',
}) => {
  const info = DIMENSION_INFO[dimension];
  const pct = score != null ? score : 0;

  const getBarColor = (s: number | null | undefined) => {
    if (s == null) return '#475569';
    if (s >= 90) return '#10B981';
    if (s >= 80) return '#3B82F6';
    if (s >= 70) return '#F59E0B';
    return '#EF4444';
  };

  const barColor = getBarColor(score);

  return (
    <div
      className={clsx(
        'card p-4 flex flex-col gap-3 hover:border-opacity-70 transition-all duration-200 hover:-translate-y-0.5',
        className
      )}
      style={{ borderColor: `${info.color}30` }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-black"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}
          >
            {info.short}
          </div>
          <div>
            <p className={clsx('font-semibold text-slate-100', size === 'sm' ? 'text-xs' : 'text-sm')}>
              {info.short === 'C' ? 'Comp. Intelligence' : info.label}
            </p>
            {weight != null && (
              <p className="text-[10px] text-slate-500">Weight: {(weight * 100).toFixed(0)}%</p>
            )}
          </div>
        </div>
        <div className="text-right">
          <p
            className={clsx('font-black', size === 'sm' ? 'text-xl' : 'text-2xl')}
            style={{ color: score != null ? barColor : '#475569' }}
          >
            {formatScore(score)}
          </p>
          <p className="text-[10px] text-slate-500">/ 100</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{
            width: `${pct}%`,
            backgroundColor: barColor,
            boxShadow: `0 0 8px ${barColor}60`,
          }}
        />
      </div>
    </div>
  );
};

export default DimensionCard;
