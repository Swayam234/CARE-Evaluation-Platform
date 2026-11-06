"""
Tool Evaluator
==============
Evaluates tool selection accuracy using benchmark expected_tool annotations.

Computes:
  - tool_selection_accuracy (did the agent call the correct tool?)

Requires:
  - Benchmark test cases with expected_tool populated
  - TestCaseResult records with actual_tool populated
"""
from typing import List
from app.services.evaluators.base_evaluator import BaseEvaluator
from app.services.kpi_calculator import RawKpiResult, calc_tool_selection_accuracy_from_results


class ToolEvaluator(BaseEvaluator):
    """
    Computes tool selection accuracy from benchmark test case results.
    """

    @property
    def name(self) -> str:
        return "tool_evaluator"

    def is_available(self) -> bool:
        return True

    def evaluate(
        self,
        run,
        traces: list,
        tool_traces: list,
        test_case_results: list,
    ) -> List[RawKpiResult]:
        return [calc_tool_selection_accuracy_from_results(test_case_results)]
