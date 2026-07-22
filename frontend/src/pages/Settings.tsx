/**
 * Settings Page – Weight configuration sliders.
 * Weights must sum to 100%.
 * Live CARE score preview.
 */
import React, { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Save, RotateCcw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { toast } from 'react-toastify';
import { configApi } from '../services/api';
import type { WeightConfig } from '../types';
import { DIMENSION_INFO } from '../types';
import CAREScoreGauge from '../components/CAREScoreGauge';

const DEFAULT_WEIGHTS = { weight_c: 25, weight_a: 30, weight_r: 30, weight_e: 15 };

interface LocalWeights {
  weight_c: number;
  weight_a: number;
  weight_r: number;
  weight_e: number;
}

const Settings: React.FC = () => {
  const [savedConfig, setSavedConfig] = useState<WeightConfig | null>(null);
  const [weights, setWeights] = useState<LocalWeights>(DEFAULT_WEIGHTS);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    configApi.getWeights()
      .then((w) => {
        setSavedConfig(w);
        setWeights({
          weight_c: Math.round(w.weight_c * 100),
          weight_a: Math.round(w.weight_a * 100),
          weight_r: Math.round(w.weight_r * 100),
          weight_e: Math.round(w.weight_e * 100),
        });
      })
      .catch(() => toast.error('Failed to load weight config'))
      .finally(() => setLoading(false));
  }, []);

  const total = weights.weight_c + weights.weight_a + weights.weight_r + weights.weight_e;
  const isValid = Math.abs(total - 100) <= 1;

  const handleSlider = (key: keyof LocalWeights, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    setWeights(DEFAULT_WEIGHTS);
    toast.info('Reset to defaults (not saved yet)');
  };

  const handleSave = async () => {
    if (!isValid) {
      toast.error(`Weights must sum to 100% (currently ${total}%)`);
      return;
    }
    setSaving(true);
    try {
      const result = await configApi.updateWeights({
        weight_c: weights.weight_c / 100,
        weight_a: weights.weight_a / 100,
        weight_r: weights.weight_r / 100,
        weight_e: weights.weight_e / 100,
      });
      setSavedConfig(result);
      toast.success('✅ Weights saved! Future evaluations will use these weights.');
    } catch (e: any) {
      toast.error(e.message || 'Failed to save weights');
    } finally {
      setSaving(false);
    }
  };

  // Compute live CARE score preview with a hypothetical score of 75 per dimension
  const previewScore = isValid
    ? (75 * weights.weight_c + 75 * weights.weight_a + 75 * weights.weight_r + 75 * weights.weight_e) / 100
    : null;

  const DIMENSION_KEYS: (keyof LocalWeights)[] = ['weight_c', 'weight_a', 'weight_r', 'weight_e'];
  const DIMS = ['c', 'a', 'r', 'e'] as const;

  if (loading) return (
    <div className="space-y-4 animate-pulse">
      {[...Array(4)].map((_, i) => <div key={i} className="card h-20" />)}
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <SettingsIcon size={24} className="text-care-c" />
        <div>
          <h1 className="text-xl font-bold text-slate-100">Settings</h1>
          <p className="text-xs text-slate-500">Configure CARE dimension weights</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card-glass p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-semibold text-slate-200">Dimension Weights</p>
              {/* Total indicator */}
              <div className={`flex items-center gap-1.5 text-sm font-bold px-3 py-1 rounded-lg ${
                isValid ? 'bg-emerald-900/30 text-emerald-400' : 'bg-red-900/30 text-red-400'
              }`}>
                {isValid
                  ? <CheckCircle2 size={14} />
                  : <AlertCircle size={14} />}
                Total: {total}%
              </div>
            </div>

            {!isValid && (
              <div className="flex items-center gap-2 p-3 bg-red-900/20 border border-red-700/30 rounded-lg mb-4 text-xs text-red-300">
                <AlertCircle size={14} />
                Weights must sum to exactly 100%. Currently {total > 100 ? 'over' : 'under'} by {Math.abs(100 - total)}%.
              </div>
            )}

            <div className="space-y-5">
              {DIMS.map((dim, idx) => {
                const key = DIMENSION_KEYS[idx];
                const info = DIMENSION_INFO[dim];
                const val = weights[key];
                return (
                  <div key={dim}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-black"
                          style={{ backgroundColor: `${info.color}20`, color: info.color }}
                        >
                          {info.short}
                        </div>
                        <span className="text-sm font-medium text-slate-200">{info.label}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={val}
                          onChange={(e) => handleSlider(key, Number(e.target.value))}
                          className="w-16 input text-center text-sm py-1"
                          id={`weight-input-${dim}`}
                        />
                        <span className="text-slate-500 text-sm">%</span>
                      </div>
                    </div>
                    <input
                      id={`weight-slider-${dim}`}
                      type="range"
                      min="0"
                      max="100"
                      step="1"
                      value={val}
                      onChange={(e) => handleSlider(key, Number(e.target.value))}
                      className="w-full h-2 rounded-full appearance-none cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, ${info.color} 0%, ${info.color} ${val}%, #1E293B ${val}%, #1E293B 100%)`,
                      }}
                    />
                    {/* Quick preset buttons */}
                    <div className="flex gap-1 mt-1.5">
                      {[10, 20, 25, 30, 40].map((pct) => (
                        <button
                          key={pct}
                          type="button"
                          onClick={() => handleSlider(key, pct)}
                          className={`text-[10px] px-1.5 py-0.5 rounded transition-colors ${
                            val === pct
                              ? 'text-white font-bold'
                              : 'text-slate-500 hover:text-slate-300'
                          }`}
                          style={val === pct ? { backgroundColor: `${info.color}30`, color: info.color } : {}}
                        >
                          {pct}%
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Weight distribution bar */}
          <div className="card p-4">
            <p className="text-xs font-semibold text-slate-400 mb-3 uppercase tracking-widest">Weight Distribution</p>
            <div className="h-6 rounded-full overflow-hidden flex">
              {DIMS.map((dim, idx) => {
                const val = weights[DIMENSION_KEYS[idx]];
                return (
                  <div
                    key={dim}
                    className="flex items-center justify-center text-[9px] font-black text-white transition-all duration-300"
                    style={{ width: `${val}%`, backgroundColor: DIMENSION_INFO[dim].color }}
                    title={`${DIMENSION_INFO[dim].label}: ${val}%`}
                  >
                    {val >= 12 ? `${val}%` : ''}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-1 text-[10px] text-slate-500">
              {DIMS.map((dim, idx) => (
                <span key={dim} style={{ color: DIMENSION_INFO[dim].color }}>
                  {DIMENSION_INFO[dim].short}: {weights[DIMENSION_KEYS[idx]]}%
                </span>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <button
              id="save-weights-btn"
              onClick={handleSave}
              disabled={!isValid || saving}
              className="btn-primary"
            >
              <Save size={16} />
              {saving ? 'Saving…' : 'Save Weights'}
            </button>
            <button
              id="reset-weights-btn"
              onClick={handleReset}
              className="btn-secondary"
            >
              <RotateCcw size={16} />
              Reset to Defaults
            </button>
          </div>
        </div>

        {/* Live Preview sidebar */}
        <div className="space-y-4">
          <div className="card-glass p-5 flex flex-col items-center gap-3">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Score Preview</p>
            <p className="text-[10px] text-slate-500 text-center">
              With all dimensions at 75/100
            </p>
            <CAREScoreGauge
              score={previewScore ?? undefined}
              size="md"
              showLabel={false}
            />
            <p className="text-xs text-slate-400">
              {isValid ? `${previewScore?.toFixed(1)} / 100` : 'Invalid weights'}
            </p>
          </div>

          {savedConfig && (
            <div className="card p-4">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">Saved Config</p>
              <div className="space-y-2">
                {DIMS.map((dim, idx) => {
                  const savedKey = `weight_${dim}` as keyof WeightConfig;
                  const savedVal = Math.round((savedConfig[savedKey] as number) * 100);
                  return (
                    <div key={dim} className="flex justify-between text-xs">
                      <span style={{ color: DIMENSION_INFO[dim].color }}>{DIMENSION_INFO[dim].label}</span>
                      <span className="text-slate-400 font-mono">{savedVal}%</span>
                    </div>
                  );
                })}
              </div>
              {savedConfig.updated_at && (
                <p className="text-[10px] text-slate-600 mt-3">
                  Last updated: {new Date(savedConfig.updated_at).toLocaleDateString()}
                </p>
              )}
            </div>
          )}

          <div className="card p-4 border-amber-700/30">
            <div className="flex items-start gap-2">
              <AlertCircle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-slate-400">
                Weight changes apply to <strong className="text-slate-300">future evaluations only</strong>.
                Historical scores are preserved with the weights active at evaluation time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
