"""
LLM Judge (Stub)
================
Architecture stub for LLM-as-a-Judge evaluation.

KPIs this evaluator is DESIGNED to produce:
  - relevance_score
  - reasoning_quality
  - completeness
  - hallucination_rate
  - planning_success_rate
  - task_decomposition_accuracy

STATUS: Not yet implemented.

To implement:
  1. Set LLM_JUDGE_PROVIDER env var to one of: openai | gemini | anthropic
  2. Set LLM_JUDGE_MODEL env var (e.g., gpt-4o, gemini-1.5-pro, claude-3-5-sonnet)
  3. Replace the stub body with prompt-based evaluation logic using the existing
     AI provider abstractions in app/config/settings.py (openai_api_key, gemini_api_key, etc.)

API keys for LLM providers are ALREADY in settings.py – do NOT add new ones.
Do NOT expose API keys in frontend code.

All KPIs return status='unavailable' until configured.
"""
import os
from typing import List
from app.services.evaluators.base_evaluator import BaseEvaluator
from app.services.kpi_calculator import RawKpiResult


_LLM_JUDGE_KPIS = [
    ("relevance_score", "/100", "Measures how relevant and on-topic the agent's responses are."),
    ("reasoning_quality", "/100", "Measures quality of reasoning chains and logical deductions."),
    ("completeness", "/100", "Measures whether responses are complete and thorough."),
    ("hallucination_rate", "percent", "Percentage of responses containing fabricated information."),
    ("planning_success_rate", "/100", "Percentage of multi-step plans successfully executed."),
    ("task_decomposition_accuracy", "/100", "Accuracy of breaking complex tasks into correct subtasks."),
]


class LlmJudge(BaseEvaluator):
    """
    LLM-as-a-Judge evaluator stub.
    Returns unavailable for all KPIs until LLM_JUDGE_PROVIDER is configured.
    """

    @property
    def name(self) -> str:
        return "llm_judge"

    def is_available(self) -> bool:
        provider = os.getenv("LLM_JUDGE_PROVIDER", "").strip()
        return bool(provider)

    def evaluate(
        self,
        run,
        traces: list,
        tool_traces: list,
        test_case_results: list,
    ) -> List[RawKpiResult]:
        provider = os.getenv("LLM_JUDGE_PROVIDER", "").strip()
        if not provider:
            note = (
                "LLM Judge not configured. Set LLM_JUDGE_PROVIDER (openai | gemini | anthropic) "
                "and LLM_JUDGE_MODEL in environment variables to enable LLM-as-a-Judge evaluation."
            )
            return [
                RawKpiResult(
                    kpi_name=kpi_name,
                    raw_value=None,
                    unit=unit,
                    source="llm_judge",
                    calculation_status="unavailable",
                    notes=note,
                )
                for kpi_name, unit, _ in _LLM_JUDGE_KPIS
            ]

        # ── Future implementation hook ──────────────────────────────────────
        # When LLM_JUDGE_PROVIDER is set, implement:
        # 1. Load test_case_results with actual_output and test_case.expected_output
        # 2. Send each pair to the LLM with a structured evaluation prompt
        # 3. Parse structured scores and return as RawKpiResult with status="calculated"
        #
        # Example prompt template:
        # "You are an AI evaluator. Rate the following response on {criterion} from 0-100.
        #  Input: {input}
        #  Expected: {expected_output}
        #  Actual: {actual_output}
        #  Return JSON: {\"score\": <int>, \"reason\": <str>}"
        #
        # Use settings.gemini_api_key / settings.openai_api_key (already in settings.py)
        # ──────────────────────────────────────────────────────────────────────

        raise NotImplementedError(
            f"LLM_JUDGE_PROVIDER='{provider}' is set but the LLM judge is not yet implemented. "
            "Implement the evaluate() method in llm_judge.py to activate."
        )
