/**
 * CARE Score Gauge Component
 * Animated semi-circular gauge with color zones and score display.
 */
import React, { useEffect, useState } from 'react';
import { getScoreColor } from '../utils';

interface CAREScoreGaugeProps {
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  recommendation?: string;
}

const SIZE_CONFIG = {
  sm: { svg: 120, r: 45, strokeWidth: 8, fontSize: 'text-2xl', subFontSize: 'text-xs' },
  md: { svg: 180, r: 68, strokeWidth: 10, fontSize: 'text-4xl', subFontSize: 'text-sm' },
  lg: { svg: 240, r: 90, strokeWidth: 12, fontSize: 'text-6xl', subFontSize: 'text-base' },
};

function getGaugeColor(score: number): string {
  if (score >= 90) return '#10B981'; // emerald
  if (score >= 80) return '#3B82F6'; // blue
  if (score >= 70) return '#F59E0B'; // amber
  return '#EF4444';                  // red
}

const CAREScoreGauge: React.FC<CAREScoreGaugeProps> = ({
  score,
  size = 'md',
  showLabel = true,
  recommendation,
}) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const config = SIZE_CONFIG[size];
  const { svg, r, strokeWidth } = config;

  const cx = svg / 2;
  const cy = svg / 2 + (size === 'sm' ? 10 : size === 'md' ? 15 : 20);

  // Semi-circle arc: circumference = π × r
  const circumference = Math.PI * r;
  const safeScore = score ?? 0;

  useEffect(() => {
    if (score == null) return;
    const timer = setTimeout(() => setAnimatedScore(safeScore), 100);
    return () => clearTimeout(timer);
  }, [score, safeScore]);

  const offset = circumference - (animatedScore / 100) * circumference;
  const color = getGaugeColor(safeScore);

  // Background track color zones (decorative)
  const zones = [
    { pct: 0.3, color: '#EF444433' },
    { pct: 0.1, color: '#F59E0B33' },
    { pct: 0.1, color: '#3B82F633' },
    { pct: 0.5, color: '#10B98133' },
  ];

  return (
    <div className="flex flex-col items-center gap-2">
      <svg
        width={svg}
        height={cy + 10}
        viewBox={`0 0 ${svg} ${cy + 10}`}
        className="overflow-visible"
      >
        {/* Background track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#1E293B"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Score arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)',
            filter: `drop-shadow(0 0 6px ${color}80)`,
          }}
        />

        {/* Glow effect overlay */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth / 3}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          opacity={0.4}
          style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)' }}
        />

        {/* Score text */}
        <text
          x={cx}
          y={cy - (size === 'sm' ? 8 : 12)}
          textAnchor="middle"
          className={`font-black ${config.fontSize}`}
          fill={score != null ? color : '#64748B'}
          style={{ fontSize: size === 'lg' ? '2.5rem' : size === 'md' ? '1.75rem' : '1.1rem', fontWeight: 900 }}
        >
          {score != null ? animatedScore.toFixed(1) : '--'}
        </text>

        {/* /100 label */}
        <text
          x={cx}
          y={cy + (size === 'sm' ? 8 : 12)}
          textAnchor="middle"
          fill="#64748B"
          style={{ fontSize: size === 'sm' ? '0.65rem' : '0.75rem' }}
        >
          / 100
        </text>

        {/* Min/Max labels */}
        <text x={cx - r - 2} y={cy + 16} textAnchor="middle" fill="#475569" style={{ fontSize: '0.6rem' }}>0</text>
        <text x={cx + r + 2} y={cy + 16} textAnchor="middle" fill="#475569" style={{ fontSize: '0.6rem' }}>100</text>
      </svg>

      {showLabel && (
        <div className="text-center">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">CARE Score</p>
          {recommendation && (
            <p className="text-sm font-semibold mt-0.5" style={{ color }}>
              {recommendation}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default CAREScoreGauge;
