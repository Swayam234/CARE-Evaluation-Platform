/**
 * KPIInput – Reusable numeric input with tooltip explaining each KPI.
 */
import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { clsx } from 'clsx';
import type { KPIDefinition } from '../types';

interface KPIInputProps {
  kpi: KPIDefinition;
  value?: string;
  onChange: (value: string) => void;
  error?: string;
}

const KPIInput: React.FC<KPIInputProps> = ({ kpi, value = '', onChange, error }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5">
        <label className="label mb-0 flex-1">
          {kpi.label}
          {kpi.lowerIsBetter && (
            <span className="ml-1.5 text-[10px] text-amber-400 font-medium">(lower is better)</span>
          )}
        </label>
        <span className="text-xs text-slate-500">{kpi.unit}</span>
        <div className="relative">
          <button
            type="button"
            className="text-slate-500 hover:text-care-c transition-colors"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            onFocus={() => setShowTooltip(true)}
            onBlur={() => setShowTooltip(false)}
            aria-label={`Help for ${kpi.label}`}
          >
            <HelpCircle size={14} />
          </button>
          {showTooltip && (
            <div className="absolute bottom-full right-0 mb-2 w-64 z-50 card-glass p-3 text-xs text-slate-300 rounded-lg shadow-card pointer-events-none">
              <p className="font-semibold text-slate-100 mb-1">{kpi.label}</p>
              <p>{kpi.tooltip}</p>
              {kpi.rawUnit && (
                <p className="mt-1 text-slate-400">Raw value in {kpi.unit}</p>
              )}
            </div>
          )}
        </div>
      </div>
      <input
        id={`kpi-${kpi.key}`}
        type="number"
        step="any"
        min={kpi.rawUnit ? undefined : 0}
        max={kpi.rawUnit ? undefined : 100}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={kpi.rawUnit ? `Enter ${kpi.unit}` : '0 – 100'}
        className={clsx('input text-sm', error && 'input-error')}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
};

export default KPIInput;
