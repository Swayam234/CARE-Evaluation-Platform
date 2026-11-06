"""
KPI Calculation Engine
======================
Computes raw KPI values from aggregated telemetry / execution data.

IMPORTANT DESIGN CONTRACT:
  - This module ONLY calculates RAW KPI values.
  - It does NOT normalize values into 0-100 CARE scores.
  - It does NOT call the CARE scoring engine.
  - Normalization remains exclusively in app/services/scoring.py.

When a KPI cannot be calculated (missing data, evaluator not configured,
business data not provided), it is returned with status="unavailable"
and raw_value=None.  It is NEVER fabricated or treated as zero.

Usage:
    from app.services.kpi_calculator import calculate_kpis_from_run
    measurements = calculate_kpis_from_run(run, traces, tool_traces, test_results, settings)
"""
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class RawKpiResult:
    """Internal representation of one computed (or unavailable) KPI."""
    kpi_name: str
    raw_value: Optional[float]       # None when unavailable
    unit: str
    source: str                      # telemetry | benchmark | llm_judge | business | evaluator
    calculation_status: str          # calculated | unavailable | error
    notes: str = ""


# ── Telemetry-derived KPI calculators ─────────────────────────────────────────

def calc_average_latency(traces: list) -> RawKpiResult:
    """
    Average latency across all task traces.
    Formula: sum(latency_ms) / number_of_traces
    """
    valid = [t.latency_ms for t in traces if t.latency_ms is not None]
    if not valid:
        return RawKpiResult(
            kpi_name="latency_ms",
            raw_value=None,
            unit="ms",
            source="telemetry",
            calculation_status="unavailable",
            notes="No latency data available in traces.",
        )
    return RawKpiResult(
        kpi_name="latency_ms",
        raw_value=round(sum(valid) / len(valid), 2),
        unit="ms",
        source="telemetry",
        calculation_status="calculated",
        notes=f"Computed from {len(valid)} traces.",
    )


def calc_failure_rate(traces: list) -> RawKpiResult:
    """
    Percentage of tasks that resulted in a failure or error.
    Formula: failed_tasks / total_tasks * 100
    """
    if not traces:
        return RawKpiResult(
            kpi_name="failure_rate",
            raw_value=None,
            unit="percent",
            source="telemetry",
            calculation_status="unavailable",
            notes="No traces available.",
        )
    failed = sum(1 for t in traces if t.status in ("failed", "error"))
    total = len(traces)
    return RawKpiResult(
        kpi_name="failure_rate",
        raw_value=round(failed / total * 100, 2),
        unit="percent",
        source="telemetry",
        calculation_status="calculated",
        notes=f"{failed} failed out of {total} tasks.",
    )


def calc_retry_rate(traces: list) -> RawKpiResult:
    """
    Percentage of tasks that required at least one retry.
    Formula: tasks_with_retry / total_tasks * 100
    """
    if not traces:
        return RawKpiResult(
            kpi_name="retry_rate",
            raw_value=None,
            unit="percent",
            source="telemetry",
            calculation_status="unavailable",
            notes="No traces available.",
        )
    retried = sum(1 for t in traces if (t.retry_count or 0) > 0)
    total = len(traces)
    return RawKpiResult(
        kpi_name="retry_rate",
        raw_value=round(retried / total * 100, 2),
        unit="percent",
        source="telemetry",
        calculation_status="calculated",
        notes=f"{retried} tasks with retries out of {total}.",
    )


def calc_tool_success_rate(tool_traces: list) -> RawKpiResult:
    """
    Percentage of tool calls that succeeded.
    Formula: successful_tool_calls / total_tool_calls * 100
    """
    if not tool_traces:
        return RawKpiResult(
            kpi_name="tool_success_rate",
            raw_value=None,
            unit="percent",
            source="telemetry",
            calculation_status="unavailable",
            notes="No tool call traces available.",
        )
    successful = sum(1 for t in tool_traces if t.status == "success")
    total = len(tool_traces)
    return RawKpiResult(
        kpi_name="tool_success_rate",
        raw_value=round(successful / total * 100, 2),
        unit="percent",
        source="telemetry",
        calculation_status="calculated",
        notes=f"{successful} successful out of {total} tool calls.",
    )


def calc_throughput(traces: list, started_at: Optional[datetime], completed_at: Optional[datetime]) -> RawKpiResult:
    """
    Tasks completed per hour.
    Formula: completed_tasks / execution_time_hours
    """
    if not traces or not started_at or not completed_at:
        return RawKpiResult(
            kpi_name="throughput",
            raw_value=None,
            unit="tasks/hr",
            source="telemetry",
            calculation_status="unavailable",
            notes="Requires run start_time, end_time, and at least one trace.",
        )
    completed = sum(1 for t in traces if t.status == "success")
    elapsed_seconds = max((completed_at - started_at).total_seconds(), 1)
    elapsed_hours = elapsed_seconds / 3600.0
    value = round(completed / elapsed_hours, 4) if elapsed_hours > 0 else None
    return RawKpiResult(
        kpi_name="throughput",
        raw_value=value,
        unit="tasks/hr",
        source="telemetry",
        calculation_status="calculated" if value is not None else "unavailable",
        notes=f"{completed} completed tasks in {elapsed_seconds:.1f}s.",
    )


def calc_token_consumption(traces: list) -> RawKpiResult:
    """
    Average total tokens consumed per task.
    Formula: total_tokens / total_tasks
    """
    valid = [t.total_tokens for t in traces if t.total_tokens is not None]
    if not valid:
        return RawKpiResult(
            kpi_name="token_consumption",
            raw_value=None,
            unit="tokens",
            source="telemetry",
            calculation_status="unavailable",
            notes="No token data available in traces.",
        )
    total_tokens = sum(valid)
    total_tasks = len(traces)
    return RawKpiResult(
        kpi_name="token_consumption",
        raw_value=round(total_tokens / total_tasks, 2),
        unit="tokens",
        source="telemetry",
        calculation_status="calculated",
        notes=f"{total_tokens} total tokens across {total_tasks} tasks.",
    )


def calc_cost_per_task(
    traces: list,
    input_cost_per_1k: Optional[float],
    output_cost_per_1k: Optional[float],
) -> RawKpiResult:
    """
    Average cost in USD per task.
    Formula: (input_tokens * input_rate + output_tokens * output_rate) / total_tasks
    """
    if input_cost_per_1k is None or output_cost_per_1k is None:
        return RawKpiResult(
            kpi_name="cost_per_task",
            raw_value=None,
            unit="USD",
            source="telemetry",
            calculation_status="unavailable",
            notes=(
                "Requires LLM_INPUT_COST_PER_1K_TOKENS and LLM_OUTPUT_COST_PER_1K_TOKENS "
                "to be set in environment variables."
            ),
        )
    costs = []
    for t in traces:
        input_t = t.input_tokens or 0
        output_t = t.output_tokens or 0
        cost = (input_t / 1000.0 * input_cost_per_1k) + (output_t / 1000.0 * output_cost_per_1k)
        costs.append(cost)
    if not costs:
        return RawKpiResult(
            kpi_name="cost_per_task",
            raw_value=None,
            unit="USD",
            source="telemetry",
            calculation_status="unavailable",
            notes="No traces available.",
        )
    return RawKpiResult(
        kpi_name="cost_per_task",
        raw_value=round(sum(costs) / len(costs), 6),
        unit="USD",
        source="telemetry",
        calculation_status="calculated",
        notes=f"Based on {len(costs)} tasks with cost rates ${input_cost_per_1k}/1k input, ${output_cost_per_1k}/1k output.",
    )


def calc_cost_per_successful_task(
    traces: list,
    input_cost_per_1k: Optional[float],
    output_cost_per_1k: Optional[float],
) -> RawKpiResult:
    """
    Average cost per successfully completed task.
    Formula: total_cost_of_successful_tasks / successful_tasks
    """
    if input_cost_per_1k is None or output_cost_per_1k is None:
        return RawKpiResult(
            kpi_name="cost_per_successful_task",
            raw_value=None,
            unit="USD",
            source="telemetry",
            calculation_status="unavailable",
            notes="Requires cost rate environment variables.",
        )
    successful_traces = [t for t in traces if t.status == "success"]
    if not successful_traces:
        return RawKpiResult(
            kpi_name="cost_per_successful_task",
            raw_value=None,
            unit="USD",
            source="telemetry",
            calculation_status="unavailable",
            notes="No successful tasks to compute cost against.",
        )
    costs = []
    for t in successful_traces:
        input_t = t.input_tokens or 0
        output_t = t.output_tokens or 0
        cost = (input_t / 1000.0 * input_cost_per_1k) + (output_t / 1000.0 * output_cost_per_1k)
        costs.append(cost)
    return RawKpiResult(
        kpi_name="cost_per_successful_task",
        raw_value=round(sum(costs) / len(costs), 6),
        unit="USD",
        source="telemetry",
        calculation_status="calculated",
        notes=f"Based on {len(costs)} successful tasks.",
    )


# ── Benchmark-derived KPI calculators ─────────────────────────────────────────

def calc_task_success_rate_from_results(test_case_results: list) -> RawKpiResult:
    """
    Task success rate from benchmark test case evaluations.
    Formula: successful_cases / total_evaluated_cases * 100
    Requires test_case_results with a populated 'success' field.
    """
    evaluated = [r for r in test_case_results if r.success is not None]
    if not evaluated:
        return RawKpiResult(
            kpi_name="task_success_rate",
            raw_value=None,
            unit="percent",
            source="benchmark",
            calculation_status="unavailable",
            notes=(
                "Requires benchmark test cases with expected_output. "
                "Either no dataset was attached or test cases have not been evaluated."
            ),
        )
    successful = sum(1 for r in evaluated if r.success)
    return RawKpiResult(
        kpi_name="task_success_rate",
        raw_value=round(successful / len(evaluated) * 100, 2),
        unit="percent",
        source="benchmark",
        calculation_status="calculated",
        notes=f"{successful} successful out of {len(evaluated)} evaluated test cases.",
    )


def calc_goal_completion_rate_from_results(test_case_results: list) -> RawKpiResult:
    """
    Goal completion rate from benchmark test case evaluations.
    Uses the same success signal as task_success_rate when a score is available,
    or treats tasks with score >= 0.7 as completed goals.
    """
    evaluated = [r for r in test_case_results if r.success is not None]
    if not evaluated:
        return RawKpiResult(
            kpi_name="goal_completion_rate",
            raw_value=None,
            unit="percent",
            source="benchmark",
            calculation_status="unavailable",
            notes="Requires benchmark evaluation results.",
        )
    # Use score >= 0.7 if available, else fall back to success boolean
    completed = sum(
        1 for r in evaluated if (r.score >= 0.7 if r.score is not None else r.success)
    )
    return RawKpiResult(
        kpi_name="goal_completion_rate",
        raw_value=round(completed / len(evaluated) * 100, 2),
        unit="percent",
        source="benchmark",
        calculation_status="calculated",
        notes=f"{completed} goals completed out of {len(evaluated)} evaluated test cases.",
    )


def calc_tool_selection_accuracy_from_results(test_case_results: list) -> RawKpiResult:
    """
    Accuracy of tool selection against benchmark expected_tool.
    Formula: correct_tool_used / cases_with_expected_tool * 100
    """
    cases_with_expected = [r for r in test_case_results if r.test_case and r.test_case.expected_tool]
    if not cases_with_expected:
        return RawKpiResult(
            kpi_name="tool_selection_accuracy",
            raw_value=None,
            unit="percent",
            source="benchmark",
            calculation_status="unavailable",
            notes="No test cases have an expected_tool specified.",
        )
    correct = sum(
        1 for r in cases_with_expected
        if r.actual_tool and r.actual_tool.strip().lower() == r.test_case.expected_tool.strip().lower()
    )
    return RawKpiResult(
        kpi_name="tool_selection_accuracy",
        raw_value=round(correct / len(cases_with_expected) * 100, 2),
        unit="percent",
        source="benchmark",
        calculation_status="calculated",
        notes=f"{correct} correct tool selections out of {len(cases_with_expected)} cases.",
    )


# ── Unavailable KPI stubs ──────────────────────────────────────────────────────

def _unavailable(kpi_name: str, unit: str, source: str, notes: str) -> RawKpiResult:
    return RawKpiResult(
        kpi_name=kpi_name,
        raw_value=None,
        unit=unit,
        source=source,
        calculation_status="unavailable",
        notes=notes,
    )


UNAVAILABLE_KPIS: List[RawKpiResult] = [
    _unavailable("relevance_score", "/100", "llm_judge",
                 "Requires an LLM-as-a-Judge evaluator. Set LLM_JUDGE_PROVIDER in environment."),
    _unavailable("reasoning_quality", "/100", "llm_judge",
                 "Requires an LLM-as-a-Judge evaluator."),
    _unavailable("completeness", "/100", "llm_judge",
                 "Requires an LLM-as-a-Judge evaluator."),
    _unavailable("planning_success_rate", "/100", "llm_judge",
                 "Requires LLM judge or manual annotation of multi-step plan outcomes."),
    _unavailable("task_decomposition_accuracy", "/100", "llm_judge",
                 "Requires LLM judge to assess subtask decomposition quality."),
    _unavailable("recommendation_acceptance_rate", "/100", "business",
                 "Requires business data: human reviewer acceptance logs."),
    _unavailable("precision", "/100", "benchmark",
                 "Requires labeled ground-truth dataset with positive/negative classification."),
    _unavailable("recall", "/100", "benchmark",
                 "Requires labeled ground-truth dataset with positive/negative classification."),
    _unavailable("hallucination_rate", "/100", "llm_judge",
                 "Requires LLM-as-a-Judge or a dedicated hallucination detection service."),
    _unavailable("consistency_score", "/100", "evaluator",
                 "Requires multiple repeated runs on identical inputs."),
    _unavailable("error_recovery_rate", "/100", "business",
                 "Requires workflow-level data on agent recovery from errors."),
    _unavailable("safety_violation_rate", "/100", "evaluator",
                 "Requires a safety guardrail service (e.g., Llama Guard, Azure AI Content Safety)."),
    _unavailable("policy_compliance_score", "/100", "evaluator",
                 "Requires a policy compliance evaluation service."),
    _unavailable("audit_coverage", "/100", "business",
                 "Requires infrastructure-level audit log completeness data."),
    _unavailable("pii_leakage_rate", "/100", "evaluator",
                 "Requires a PII detection service."),
    _unavailable("resource_utilization", "/100", "infrastructure",
                 "Requires infrastructure metrics (CPU/GPU/memory utilization)."),
    _unavailable("human_effort_saved", "/100", "business",
                 "Requires business measurement of time saved vs. manual process."),
    _unavailable("productivity_improvement", "percent", "business",
                 "Requires business productivity baseline and measured output."),
    _unavailable("business_roi", "percent", "business",
                 "Requires total cost of ownership and business value attribution."),
    _unavailable("payback_period_months", "months", "business",
                 "Requires investment data and monthly value generated."),
]


# ── Top-level entry point ─────────────────────────────────────────────────────

def calculate_kpis_from_run(
    run,                        # EvaluationRun ORM object
    traces: list,               # List[AgentTrace]
    tool_traces: list,          # List[ToolTrace]
    test_case_results: list,    # List[TestCaseResult] (may be empty)
    input_cost_per_1k: Optional[float] = None,
    output_cost_per_1k: Optional[float] = None,
) -> List[RawKpiResult]:
    """
    Calculate all KPI values for an Evaluation Run.
    Returns a list of RawKpiResult objects – one per CARE KPI.
    KPIs that cannot be computed have raw_value=None and status="unavailable".
    """
    results: List[RawKpiResult] = []

    # ── Telemetry-derived KPIs ─────────────────────────────────────────────
    results.append(calc_average_latency(traces))
    results.append(calc_failure_rate(traces))
    results.append(calc_retry_rate(traces))
    results.append(calc_tool_success_rate(tool_traces))
    results.append(calc_throughput(traces, run.started_at, run.completed_at))
    results.append(calc_token_consumption(traces))
    results.append(calc_cost_per_task(traces, input_cost_per_1k, output_cost_per_1k))
    results.append(calc_cost_per_successful_task(traces, input_cost_per_1k, output_cost_per_1k))

    # ── Benchmark-derived KPIs ─────────────────────────────────────────────
    results.append(calc_task_success_rate_from_results(test_case_results))
    results.append(calc_goal_completion_rate_from_results(test_case_results))
    results.append(calc_tool_selection_accuracy_from_results(test_case_results))

    # ── Unavailable KPIs (documented) ─────────────────────────────────────
    results.extend(UNAVAILABLE_KPIS)

    return results
