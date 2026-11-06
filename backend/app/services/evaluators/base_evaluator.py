"""
Base Evaluator
==============
Abstract base class for all CARE evaluators.
Concrete evaluators implement evaluate() and return a list of KPI measurements.
"""
from abc import ABC, abstractmethod
from typing import List
from app.services.kpi_calculator import RawKpiResult


class BaseEvaluator(ABC):
    """
    Abstract base for CARE evaluators.

    Each evaluator is responsible for computing one or more KPIs that CANNOT
    be derived from raw telemetry alone (e.g., accuracy, safety, reasoning quality).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable evaluator name."""

    @abstractmethod
    def evaluate(
        self,
        run,                      # EvaluationRun ORM object
        traces: list,             # List[AgentTrace]
        tool_traces: list,        # List[ToolTrace]
        test_case_results: list,  # List[TestCaseResult]
    ) -> List[RawKpiResult]:
        """
        Compute KPI measurements for a given evaluation run.
        Must NOT return None for any KPI – use status='unavailable' instead.
        """

    def is_available(self) -> bool:
        """
        Returns True if this evaluator is configured and ready.
        Subclasses override this to check env vars or service availability.
        """
        return True
