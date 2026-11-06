"""
Accuracy Evaluator
==================
Evaluates task-level accuracy using benchmark test case results.

Computes:
  - task_success_rate   (binary: did the agent produce the expected output?)
  - goal_completion_rate (score-weighted variant of task success)

Requires:
  - Benchmark test cases with expected_output attached to the run
  - TestCaseResult records with the 'success' field populated
"""
from typing import List
from app.services.evaluators.base_evaluator import BaseEvaluator
from app.services.kpi_calculator import (
    RawKpiResult,
    calc_task_success_rate_from_results,
    calc_goal_completion_rate_from_results,
)


class AccuracyEvaluator(BaseEvaluator):
    """
    Computes accuracy KPIs from benchmark test case results.
    Does NOT require an LLM judge – uses exact-match or pre-computed success flags.
    """

    @property
    def name(self) -> str:
        return "accuracy_evaluator"

    def is_available(self) -> bool:
        # Always available – does not require external services
        return True

    def evaluate(
        self,
        run,
        traces: list,
        tool_traces: list,
        test_case_results: list,
    ) -> List[RawKpiResult]:
        results = []
        results.append(calc_task_success_rate_from_results(test_case_results))
        results.append(calc_goal_completion_rate_from_results(test_case_results))
        return results
