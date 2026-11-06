"""
SQLAlchemy ORM Models – Automated Evaluation Pipeline
=====================================================
New tables for the automated evaluation pipeline.
All tables are additive – no existing tables are modified or dropped.

Tables:
  evaluation_runs     – top-level run records
  agent_traces        – one row per task execution
  tool_traces         – one row per tool call within a task
  kpi_measurements    – calculated KPI values with source metadata
  evaluation_datasets – benchmark dataset metadata
  evaluation_test_cases – individual test cases in a dataset
  test_case_results   – agent output vs expected (per test case per run)
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Text, DateTime,
    ForeignKey, Boolean, JSON,
)
from sqlalchemy.orm import relationship
from app.database.database import Base


class EvaluationRun(Base):
    """
    Top-level record for one automated evaluation run.
    When completed, optionally links to an Evaluation record
    produced by the existing CARE scoring engine.
    """
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    dataset_name = Column(String(255), nullable=True)
    dataset_id = Column(Integer, ForeignKey("evaluation_datasets.id", ondelete="SET NULL"), nullable=True)
    total_tasks = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING | RUNNING | COMPLETED | FAILED
    error_message = Column(Text, nullable=True)
    # Cost configuration captured at run time (optional – used by KPI calculator)
    llm_input_cost_per_1k = Column(Float, nullable=True)
    llm_output_cost_per_1k = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # FK to the Evaluation produced by the CARE scoring engine (set after generate-evaluation)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    agent_traces = relationship("AgentTrace", back_populates="evaluation_run", cascade="all, delete-orphan")
    kpi_measurements = relationship("KpiMeasurement", back_populates="evaluation_run", cascade="all, delete-orphan")
    test_case_results = relationship("TestCaseResult", back_populates="evaluation_run", cascade="all, delete-orphan")
    dataset = relationship("EvaluationDataset", foreign_keys=[dataset_id])


class AgentTrace(Base):
    """
    One trace record per task executed during an Evaluation Run.
    Captures latency, token usage, status, and error information.
    """
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(Integer, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    trace_id = Column(String(255), nullable=True, index=True)   # OTel trace ID
    task_id = Column(String(255), nullable=True, index=True)    # application-level task ID
    model_name = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    latency_ms = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="unknown")  # success | failed | error | unknown
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    raw_metadata = Column(JSON, nullable=True)   # catch-all for extra OTel attributes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    evaluation_run = relationship("EvaluationRun", back_populates="agent_traces")
    tool_traces = relationship("ToolTrace", back_populates="agent_trace", cascade="all, delete-orphan")


class ToolTrace(Base):
    """
    One row per tool call within a task trace.
    """
    __tablename__ = "tool_traces"

    id = Column(Integer, primary_key=True, index=True)
    agent_trace_id = Column(Integer, ForeignKey("agent_traces.id", ondelete="CASCADE"), nullable=False, index=True)
    trace_id = Column(String(255), nullable=True)    # parent OTel trace ID
    tool_name = Column(String(255), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    latency_ms = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="unknown")  # success | failed | error | unknown
    error_message = Column(Text, nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent_trace = relationship("AgentTrace", back_populates="tool_traces")


class KpiMeasurement(Base):
    """
    Stores one KPI value per metric per Evaluation Run.
    Includes the source of the measurement and its calculation status
    so the UI can display full source transparency.

    calculation_status:
      calculated  – value was successfully computed
      unavailable – cannot be computed (missing data / evaluator not configured)
      error       – computation attempted but failed
    """
    __tablename__ = "kpi_measurements"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(Integer, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_name = Column(String(100), nullable=False)
    raw_value = Column(Float, nullable=True)            # null when unavailable
    unit = Column(String(50), nullable=True)
    source = Column(String(100), nullable=True)         # e.g. "telemetry", "benchmark", "llm_judge", "business"
    calculation_status = Column(String(20), nullable=False, default="unavailable")
    notes = Column(Text, nullable=True)                 # human-readable explanation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    evaluation_run = relationship("EvaluationRun", back_populates="kpi_measurements")


class EvaluationDataset(Base):
    """
    A named collection of benchmark test cases.
    """
    __tablename__ = "evaluation_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_cases = relationship("EvaluationTestCase", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationTestCase(Base):
    """
    A single benchmark test case within a dataset.
    expected_output and expected_tool are used by accuracy / tool evaluators.
    """
    __tablename__ = "evaluation_test_cases"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(255), nullable=True, index=True)   # matches AgentTrace.task_id
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    expected_tool = Column(String(255), nullable=True)          # expected tool name
    extra_metadata = Column(JSON, nullable=True)                # renamed from 'metadata' (SQLAlchemy reserved)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="test_cases")
    results = relationship("TestCaseResult", back_populates="test_case", cascade="all, delete-orphan")


class TestCaseResult(Base):
    """
    Stores the agent's output for a specific test case within an Evaluation Run.
    The accuracy_evaluator uses this to compute task_success_rate.
    """
    __tablename__ = "test_case_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(Integer, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("evaluation_test_cases.id", ondelete="CASCADE"), nullable=False)
    actual_output = Column(Text, nullable=True)
    actual_tool = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=True)           # null = not yet evaluated
    evaluator_used = Column(String(100), nullable=True)  # e.g. "exact_match", "llm_judge"
    score = Column(Float, nullable=True)               # optional fine-grained score 0-1
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    evaluation_run = relationship("EvaluationRun", back_populates="test_case_results")
    test_case = relationship("EvaluationTestCase", back_populates="results")
