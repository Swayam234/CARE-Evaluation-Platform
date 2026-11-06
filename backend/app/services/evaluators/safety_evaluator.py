"""
Safety Evaluator (Stub)
=======================
Architecture stub for safety-related KPI evaluation.

KPIs this evaluator is DESIGNED to produce:
  - safety_violation_rate
  - policy_compliance_score
  - pii_leakage_rate

STATUS: Not yet implemented.

To implement, replace this stub with a real safety service integration:
  - Llama Guard (Meta)
  - Azure AI Content Safety
  - AWS Comprehend (for PII detection)
  - Custom guardrail service

All KPIs return status='unavailable' until a real evaluator is configured.
Configure via: SAFETY_EVALUATOR_PROVIDER env var (currently unused stub).
"""
from typing import List
from app.services.evaluators.base_evaluator import BaseEvaluator
from app.services.kpi_calculator import RawKpiResult


class SafetyEvaluator(BaseEvaluator):
    """
    Stub safety evaluator.
    Returns unavailable status for all safety KPIs until a real provider is configured.
    """

    @property
    def name(self) -> str:
        return "safety_evaluator"

    def is_available(self) -> bool:
        # Future: check SAFETY_EVALUATOR_PROVIDER env var
        return False

    def evaluate(
        self,
        run,
        traces: list,
        tool_traces: list,
        test_case_results: list,
    ) -> List[RawKpiResult]:
        _STUB_NOTE = (
            "Safety evaluator not configured. To enable, implement a safety guardrail "
            "service and set SAFETY_EVALUATOR_PROVIDER in environment variables."
        )
        return [
            RawKpiResult(
                kpi_name="safety_violation_rate",
                raw_value=None,
                unit="percent",
                source="evaluator",
                calculation_status="unavailable",
                notes=_STUB_NOTE,
            ),
            RawKpiResult(
                kpi_name="policy_compliance_score",
                raw_value=None,
                unit="/100",
                source="evaluator",
                calculation_status="unavailable",
                notes=_STUB_NOTE,
            ),
            RawKpiResult(
                kpi_name="pii_leakage_rate",
                raw_value=None,
                unit="percent",
                source="evaluator",
                calculation_status="unavailable",
                notes=(
                    "PII detection not configured. Requires a PII detection service "
                    "such as AWS Comprehend, Microsoft Presidio, or equivalent."
                ),
            ),
        ]
