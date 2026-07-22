/**
 * NewEvaluation Page – Multi-step wizard (6 steps)
 * Step 1: Agent Info
 * Step 2: Computational Intelligence KPIs
 * Step 3: Accuracy KPIs
 * Step 4: Reliability KPIs
 * Step 5: Economics KPIs
 * Step 6: Review & Submit
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import {
  Brain, Target, Shield, DollarSign, FileCheck, ChevronRight, ChevronLeft,
  CheckCircle, Bot, Loader2, HelpCircle,
} from 'lucide-react';
import { clsx } from 'clsx';
import { evaluationsApi } from '../services/api';
import type { EvaluationFormData } from '../types';
import { KPI_DEFINITIONS, DIMENSION_INFO } from '../types';
import { buildEvaluationPayload } from '../utils';
import CAREScoreGauge from '../components/CAREScoreGauge';

const STEPS = [
  { id: 1, label: 'Agent Info', icon: <Bot size={16} />, description: 'Basic agent metadata' },
  { id: 2, label: 'Intelligence', icon: <Brain size={16} />, description: 'Computational Intelligence KPIs', dim: 'c' as const },
  { id: 3, label: 'Accuracy', icon: <Target size={16} />, description: 'Accuracy KPIs', dim: 'a' as const },
  { id: 4, label: 'Reliability', icon: <Shield size={16} />, description: 'Reliability KPIs', dim: 'r' as const },
  { id: 5, label: 'Economics', icon: <DollarSign size={16} />, description: 'Economics KPIs', dim: 'e' as const },
  { id: 6, label: 'Review', icon: <FileCheck size={16} />, description: 'Review & Submit' },
];

const AGENT_TYPES = [
  'Chatbot', 'RAG Agent', 'Coding Assistant', 'Workflow Automation',
  'Customer Support', 'Sales Agent', 'HR Agent', 'Finance Agent', 'Research Agent', 'Other',
];

// Inline KPI field to avoid react-hook-form + KPIInput register conflicts
interface KPIFieldProps {
  kpi: typeof KPI_DEFINITIONS[0];
  register: any;
  value: string | undefined;
}
const KPIField: React.FC<KPIFieldProps> = ({ kpi, register, value }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5">
        <label htmlFor={`kpi-${kpi.key}`} className="label mb-0 flex-1 text-sm">
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
          >
            <HelpCircle size={14} />
          </button>
          {showTooltip && (
            <div className="absolute bottom-full right-0 mb-2 w-64 z-50 card-glass p-3 text-xs text-slate-300 rounded-lg shadow-card pointer-events-none">
              <p className="font-semibold text-slate-100 mb-1">{kpi.label}</p>
              <p>{kpi.tooltip}</p>
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
        placeholder={kpi.rawUnit ? `Enter ${kpi.unit}` : '0 – 100'}
        className="input text-sm"
        {...register(kpi.key)}
      />
    </div>
  );
};

const NewEvaluation: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<EvaluationFormData>({
    mode: 'onBlur',
  });

  const formValues = watch();

  const kpisForStep = (stepId: number) => {
    const dimMap: Record<number, string> = { 2: 'c', 3: 'a', 4: 'r', 5: 'e' };
    const dim = dimMap[stepId];
    if (!dim) return [];
    return KPI_DEFINITIONS.filter((k) => k.dimension === dim);
  };

  const onSubmit = async (data: EvaluationFormData) => {
    setSubmitting(true);
    try {
      const payload = buildEvaluationPayload(data);
      const result = await evaluationsApi.create(payload);
      toast.success(`🎯 ${result.agent_name} evaluated! CARE Score: ${result.care_score?.toFixed(1) ?? 'N/A'}`);
      navigate(`/results/${result.id}`);
    } catch (e: any) {
      toast.error(e.message || 'Failed to submit evaluation');
    } finally {
      setSubmitting(false);
    }
  };

  const goNext = () => { if (currentStep < STEPS.length) setCurrentStep((s) => s + 1); };
  const goPrev = () => { if (currentStep > 1) setCurrentStep((s) => s - 1); };

  const stepInfo = STEPS[currentStep - 1];
  const isLastStep = currentStep === STEPS.length;

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Step Progress Indicator */}
      <div className="card-glass p-4 mb-6">
        <div className="flex items-center justify-between">
          {STEPS.map((step, idx) => {
            const isCompleted = currentStep > step.id;
            const isActive = currentStep === step.id;
            const dimInfo = step.dim ? DIMENSION_INFO[step.dim] : null;
            return (
              <React.Fragment key={step.id}>
                <div
                  className="flex flex-col items-center gap-1 cursor-pointer"
                  onClick={() => setCurrentStep(step.id)}
                >
                  <div
                    className={clsx(
                      'w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300',
                      isCompleted
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : isActive
                        ? ''
                        : 'bg-bg-hover text-slate-500'
                    )}
                    style={
                      isActive
                        ? { backgroundColor: `${dimInfo?.color ?? '#6366F1'}20`, color: dimInfo?.color ?? '#6366F1' }
                        : {}
                    }
                  >
                    {isCompleted ? <CheckCircle size={18} /> : step.icon}
                  </div>
                  <span
                    className={clsx(
                      'text-[10px] font-semibold hidden sm:block',
                      isActive ? 'text-slate-100' : isCompleted ? 'text-emerald-400' : 'text-slate-500'
                    )}
                  >
                    {step.label}
                  </span>
                </div>
                {idx < STEPS.length - 1 && (
                  <div
                    className={clsx(
                      'flex-1 h-0.5 mx-2 rounded transition-all duration-500',
                      isCompleted ? 'bg-emerald-500/50' : 'bg-bg-border'
                    )}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
        <div className="mt-3 text-center">
          <p className="text-xs text-slate-500">
            Step {currentStep} of {STEPS.length} —{' '}
            <span className="text-slate-300">{stepInfo.description}</span>
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main form panel */}
          <div className="lg:col-span-2 card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={
                  stepInfo.dim
                    ? { backgroundColor: `${DIMENSION_INFO[stepInfo.dim].color}20`, color: DIMENSION_INFO[stepInfo.dim].color }
                    : { backgroundColor: '#6366F120', color: '#6366F1' }
                }
              >
                {stepInfo.icon}
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-100">{stepInfo.label}</h2>
                <p className="text-xs text-slate-500">{stepInfo.description}</p>
              </div>
            </div>

            {/* Step 1: Agent Info */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="label" htmlFor="agent_name">Agent Name *</label>
                  <input
                    id="agent_name"
                    className={clsx('input', errors.agent_name && 'input-error')}
                    placeholder="e.g. Resume Screening Agent v2"
                    {...register('agent_name', { required: 'Agent name is required' })}
                  />
                  {errors.agent_name && (
                    <p className="text-xs text-red-400 mt-1">{errors.agent_name.message}</p>
                  )}
                </div>
                <div>
                  <label className="label" htmlFor="agent_type">Agent Type *</label>
                  <select
                    id="agent_type"
                    className={clsx('input', errors.agent_type && 'input-error')}
                    {...register('agent_type', { required: 'Agent type is required' })}
                  >
                    <option value="">Select type…</option>
                    {AGENT_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  {errors.agent_type && (
                    <p className="text-xs text-red-400 mt-1">{errors.agent_type.message}</p>
                  )}
                </div>
                <div>
                  <label className="label" htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    rows={3}
                    className="input resize-none"
                    placeholder="Briefly describe what this agent does…"
                    {...register('description')}
                  />
                </div>
                <div>
                  <label className="label" htmlFor="evaluator">Evaluator Name</label>
                  <input
                    id="evaluator"
                    className="input"
                    placeholder="Your name or team"
                    {...register('evaluator')}
                  />
                </div>
              </div>
            )}

            {/* Steps 2–5: KPI inputs */}
            {currentStep >= 2 && currentStep <= 5 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {kpisForStep(currentStep).map((kpi) => (
                  <KPIField key={kpi.key} kpi={kpi} register={register} value={formValues[kpi.key as keyof EvaluationFormData] as string} />
                ))}
              </div>
            )}

            {/* Step 6: Review */}
            {currentStep === 6 && (
              <div className="space-y-4">
                <div className="card p-4">
                  <p className="text-sm font-semibold text-slate-300 mb-3">Agent Information</p>
                  <div className="grid grid-cols-2 gap-y-2 text-sm">
                    <span className="text-slate-500">Name:</span>
                    <span className="text-slate-100 font-medium">{formValues.agent_name || '–'}</span>
                    <span className="text-slate-500">Type:</span>
                    <span className="text-slate-100">{formValues.agent_type || '–'}</span>
                    <span className="text-slate-500">Description:</span>
                    <span className="text-slate-100">{formValues.description || '–'}</span>
                    <span className="text-slate-500">Evaluator:</span>
                    <span className="text-slate-100">{formValues.evaluator || '–'}</span>
                  </div>
                </div>
                {(['c', 'a', 'r', 'e'] as const).map((dim) => {
                  const dimKPIs = KPI_DEFINITIONS.filter((k) => k.dimension === dim);
                  const provided = dimKPIs.filter(
                    (k) => formValues[k.key as keyof EvaluationFormData]
                  );
                  return (
                    <div
                      key={dim}
                      className="card p-4"
                      style={{ borderColor: `${DIMENSION_INFO[dim].color}30` }}
                    >
                      <p
                        className="text-sm font-semibold mb-2"
                        style={{ color: DIMENSION_INFO[dim].color }}
                      >
                        {DIMENSION_INFO[dim].label} ({provided.length}/{dimKPIs.length} KPIs provided)
                      </p>
                      {provided.length === 0 ? (
                        <p className="text-xs text-slate-500 italic">No KPIs entered for this dimension.</p>
                      ) : (
                        <div className="grid grid-cols-2 gap-y-1 text-xs">
                          {provided.map((k) => (
                            <React.Fragment key={k.key}>
                              <span className="text-slate-500">{k.label}:</span>
                              <span className="text-slate-200">
                                {formValues[k.key as keyof EvaluationFormData]} {k.unit}
                              </span>
                            </React.Fragment>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Sidebar: live coverage preview */}
          <div className="space-y-4">
            <div className="card-glass p-5 flex flex-col items-center gap-3">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Score Preview</p>
              <CAREScoreGauge size="md" showLabel={false} />
              <p className="text-xs text-slate-500 text-center">
                Calculated upon submission
              </p>
            </div>

            <div className="card p-4 space-y-3">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest">KPI Coverage</p>
              {(['c', 'a', 'r', 'e'] as const).map((dim) => {
                const dimKPIs = KPI_DEFINITIONS.filter((k) => k.dimension === dim);
                const provided = dimKPIs.filter(
                  (k) => formValues[k.key as keyof EvaluationFormData]
                ).length;
                const pct = Math.round((provided / dimKPIs.length) * 100);
                return (
                  <div key={dim}>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: DIMENSION_INFO[dim].color }}>
                        {DIMENSION_INFO[dim].short} – {DIMENSION_INFO[dim].label}
                      </span>
                      <span className="text-slate-500">{provided}/{dimKPIs.length}</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${pct}%`, backgroundColor: DIMENSION_INFO[dim].color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="card p-3 border-amber-700/30">
              <p className="text-xs text-slate-400">
                💡 <strong className="text-slate-300">Tip:</strong> You can leave KPIs empty. The scoring engine
                will compute dimension scores only from provided KPIs.
              </p>
            </div>
          </div>
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between mt-6">
          <button
            type="button"
            onClick={goPrev}
            disabled={currentStep === 1}
            className="btn-secondary"
          >
            <ChevronLeft size={16} />
            Previous
          </button>

          {isLastStep ? (
            <button type="submit" disabled={submitting} className="btn-primary">
              {submitting ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Submitting…
                </>
              ) : (
                <>
                  <CheckCircle size={16} />
                  Submit Evaluation
                </>
              )}
            </button>
          ) : (
            <button type="button" onClick={goNext} className="btn-primary">
              Next Step
              <ChevronRight size={16} />
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default NewEvaluation;
