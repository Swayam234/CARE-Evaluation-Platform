"""
Pydantic Schemas – Automated Evaluation Pipeline
=================================================
Validation schemas for all pipeline API endpoints.
Follows the same conventions as app/schemas/evaluation.py.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────────────

class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TraceStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"
    UNKNOWN = "unknown"


class CalculationStatus(str, Enum):
    CALCULATED = "calculated"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


# ── Evaluation Run Schemas ────────────────────────────────────────────────────

class EvaluationRunCreate(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    dataset_name: Optional[str] = Field(None, max_length=255)
    dataset_id: Optional[int] = None
    total_tasks: Optional[int] = Field(None, ge=0)
    # Optional cost config for this run (overrides env vars if set)
    llm_input_cost_per_1k: Optional[float] = Field(None, ge=0, description="Input token cost per 1000 tokens in USD")
    llm_output_cost_per_1k: Optional[float] = Field(None, ge=0, description="Output token cost per 1000 tokens in USD")


class EvaluationRunRead(BaseModel):
    id: int
    agent_name: str
    agent_type: str
    description: Optional[str]
    dataset_name: Optional[str]
    dataset_id: Optional[int]
    total_tasks: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    evaluation_id: Optional[int]
    llm_input_cost_per_1k: Optional[float]
    llm_output_cost_per_1k: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvaluationRunSummary(BaseModel):
    id: int
    agent_name: str
    agent_type: str
    status: str
    total_tasks: Optional[int]
    dataset_name: Optional[str]
    evaluation_id: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Agent Trace Schemas ───────────────────────────────────────────────────────

class AgentTraceCreate(BaseModel):
    """
    Schema for ingesting one task execution trace.
    Maps to OpenTelemetry span attributes where applicable.
    """
    model_config = {"protected_namespaces": ()}  # allow 'model_name' field

    trace_id: Optional[str] = Field(None, max_length=255, description="OTel trace ID")
    task_id: Optional[str] = Field(None, max_length=255, description="Application-level task ID")
    model_name: Optional[str] = Field(None, max_length=255)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    latency_ms: Optional[float] = Field(None, ge=0)
    status: TraceStatus = TraceStatus.UNKNOWN
    input_tokens: Optional[int] = Field(None, ge=0)
    output_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    retry_count: int = Field(0, ge=0)
    raw_metadata: Optional[Dict[str, Any]] = None


class AgentTraceRead(AgentTraceCreate):
    id: int
    evaluation_run_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentTraceBulkCreate(BaseModel):
    """Bulk trace ingestion – accepts a list of traces in one request."""
    traces: List[AgentTraceCreate] = Field(..., min_length=1, max_length=1000)


# ── Tool Trace Schemas ────────────────────────────────────────────────────────

class ToolTraceCreate(BaseModel):
    """Schema for ingesting one tool call trace."""
    trace_id: Optional[str] = Field(None, max_length=255)
    tool_name: str = Field(..., min_length=1, max_length=255)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    latency_ms: Optional[float] = Field(None, ge=0)
    status: TraceStatus = TraceStatus.UNKNOWN
    error_message: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None


class ToolTraceRead(ToolTraceCreate):
    id: int
    agent_trace_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ToolTraceBulkCreate(BaseModel):
    """Bulk tool trace ingestion – keyed by agent trace ID."""
    agent_trace_id: int
    tool_traces: List[ToolTraceCreate] = Field(..., min_length=1, max_length=500)


# ── KPI Measurement Schemas ───────────────────────────────────────────────────

class KpiMeasurementRead(BaseModel):
    """
    Read schema for a single KPI measurement.
    Includes source and calculation_status for full transparency.
    """
    id: int
    evaluation_run_id: int
    kpi_name: str
    raw_value: Optional[float]          # null = unavailable; NEVER treat as zero
    unit: Optional[str]
    source: Optional[str]               # telemetry | benchmark | llm_judge | business | evaluator
    calculation_status: str             # calculated | unavailable | error
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class KpiCoverageStats(BaseModel):
    """Summary of KPI coverage for a run."""
    total_kpis: int
    calculated: int
    unavailable: int
    error: int
    coverage_percent: float             # calculated / total_kpis * 100


# ── Dataset Schemas ───────────────────────────────────────────────────────────

class EvaluationDatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class EvaluationDatasetRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    test_case_count: Optional[int] = None

    class Config:
        from_attributes = True


# ── Test Case Schemas ─────────────────────────────────────────────────────────

class EvaluationTestCaseCreate(BaseModel):
    task_id: Optional[str] = Field(None, max_length=255)
    input: str = Field(..., min_length=1)
    expected_output: Optional[str] = None
    expected_tool: Optional[str] = Field(None, max_length=255)
    extra_metadata: Optional[Dict[str, Any]] = None  # renamed from 'metadata' (reserved in SQLAlchemy)


class EvaluationTestCaseRead(BaseModel):
    id: int
    dataset_id: int
    task_id: Optional[str]
    input: str
    expected_output: Optional[str]
    expected_tool: Optional[str]
    extra_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class TestCaseBulkCreate(BaseModel):
    test_cases: List[EvaluationTestCaseCreate] = Field(..., min_length=1, max_length=10000)


# ── Test Case Result Schemas ──────────────────────────────────────────────────

class TestCaseResultCreate(BaseModel):
    test_case_id: int
    actual_output: Optional[str] = None
    actual_tool: Optional[str] = Field(None, max_length=255)
    success: Optional[bool] = None
    evaluator_used: Optional[str] = Field(None, max_length=100)
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class TestCaseResultRead(BaseModel):
    id: int
    evaluation_run_id: int
    test_case_id: int
    actual_output: Optional[str]
    actual_tool: Optional[str]
    success: Optional[bool]
    evaluator_used: Optional[str]
    score: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TestCaseResultBulkCreate(BaseModel):
    results: List[TestCaseResultCreate] = Field(..., min_length=1, max_length=10000)


# ── Response Schemas ──────────────────────────────────────────────────────────

class RunStatusResponse(BaseModel):
    run_id: int
    status: str
    agent_name: str
    total_tasks: Optional[int]
    trace_count: int
    tool_trace_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    evaluation_id: Optional[int]
    error_message: Optional[str]


class KpiCalculationResponse(BaseModel):
    run_id: int
    measurements: List[KpiMeasurementRead]
    coverage: KpiCoverageStats
    message: str


class GenerateEvaluationResponse(BaseModel):
    run_id: int
    evaluation_id: int
    care_score: Optional[float]
    score_c: Optional[float]
    score_a: Optional[float]
    score_r: Optional[float]
    score_e: Optional[float]
    recommendation: Optional[str]
    kpi_coverage: KpiCoverageStats
    message: str


class SimulationConfig(BaseModel):
    """
    Configuration for the built-in simulation adapter.
    Clearly labeled as SIMULATION – not a real agent.
    """
    agent_name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = "Simulated evaluation run (NOT a real agent)"
    num_tasks: int = Field(10, ge=1, le=1000)
    success_rate: float = Field(0.85, ge=0.0, le=1.0, description="Fraction of tasks that succeed")
    avg_latency_ms: float = Field(750.0, ge=10.0, description="Average simulated latency per task in ms")
    latency_variance_pct: float = Field(0.3, ge=0.0, le=1.0, description="Latency variance as fraction of avg")
    avg_input_tokens: int = Field(500, ge=1)
    avg_output_tokens: int = Field(300, ge=1)
    tool_call_rate: float = Field(0.7, ge=0.0, le=1.0, description="Fraction of tasks that make tool calls")
    tool_success_rate: float = Field(0.92, ge=0.0, le=1.0)
    retry_rate: float = Field(0.08, ge=0.0, le=1.0)
    llm_input_cost_per_1k: Optional[float] = Field(0.0005, ge=0)
    llm_output_cost_per_1k: Optional[float] = Field(0.0015, ge=0)
    dataset_id: Optional[int] = None
    # Simulation label fields – always present
    is_simulation: bool = True
    simulation_label: str = "SIMULATED – synthetic traces, not a real agent execution"
