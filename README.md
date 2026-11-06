# 🛡️ CARE Evaluation Platform

> **Enterprise Agentic AI Evaluation Framework & Benchmarking System**
> Standardizing the evaluation of Autonomous AI Agents across **Computational Intelligence**, **Accuracy**, **Reliability**, and **Economics**.

---

## 📋 Table of Contents

- [Overview & Purpose](#-overview--purpose)
- [The CARE Evaluation Framework](#-the-care-evaluation-framework)
  - [Dimension Breakdown & Weights](#dimension-breakdown--weights)
  - [CARE Score Formula & Normalization](#care-score-formula--normalization)
  - [Deployment Recommendation Tiers](#deployment-recommendation-tiers)
- [⚡ Automated AI-Agent Evaluation Pipeline](#-automated-ai-agent-evaluation-pipeline)
  - [Pipeline Architecture](#pipeline-architecture)
  - [KPI Source Classification & Transparency](#kpi-source-classification--transparency)
  - [Evaluator Abstraction Architecture](#evaluator-abstraction-architecture)
  - [Ingesting Traces from Real Agents](#ingesting-traces-from-real-agents)
  - [Simulation Adapter (Demo Mode)](#simulation-adapter-demo-mode)
  - [Secret Protection & Telemetry Exporters](#secret-protection--telemetry-exporters)
- [Key Features](#-key-features)
- [System Architecture & Technology Stack](#-system-architecture--technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Local Setup Guide](#-installation--local-setup-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup (FastAPI)](#1-backend-setup-fastapi)
  - [Frontend Setup (React + Vite)](#2-frontend-setup-react--vite)
- [API Documentation Reference](#-api-documentation-reference)
- [Database Schema & Data Models](#-database-schema--data-models)
- [Automated Recommendation Engine](#-automated-recommendation-engine)
- [Reporting & Data Export](#-reporting--data-export)
- [Development & Testing](#-development--testing)

---

## 🌟 Overview & Purpose

As enterprise adoption of LLM-powered Autonomous AI Agents accelerates, organizations face a critical challenge: **How do we quantitatively evaluate, compare, and determine production-readiness for AI agents?**

The **CARE Evaluation Platform** is a full-stack, enterprise-grade benchmarking application designed to measure AI agent performance across 31 holistic Key Performance Indicators (KPIs). By synthesizing multi-dimensional evaluations into a unified **CARE Score (0–100)**, the platform empowers AI engineers, product managers, and enterprise leaders to:

- 📊 **Benchmark AI Agents** before deploying to production environments.
- 🆚 **Compare Agent Models Side-by-Side** across intelligence, accuracy, safety, and operational cost.
- 🎯 **Identify Performance Bottlenecks** with automated diagnostic recommendations.
- ⚙️ **Customize Evaluation Criteria Weights** to align with organization-specific business priorities.
- 📑 **Export Executive PDF & CSV Reports** for audit compliance and governance.

---

## 🧠 The CARE Evaluation Framework

The CARE framework evaluates AI agents across four foundational dimensions:

```
                  ┌─────────────────────────────────────────┐
                  │          CARE Score (0 - 100)           │
                  └────────────────────┬────────────────────┘
                                       │
      ┌────────────────────┬───────────┴───────────┬────────────────────┐
      ▼                    ▼                       ▼                    ▼
┌───────────┐        ┌───────────┐           ┌───────────┐        ┌───────────┐
│     C     │        │     A     │           │     R     │        │     E     │
│Compu. Intel│       │ Accuracy  │           │Reliability│        │ Economics │
│   (25%)   │        │   (30%)   │           │   (30%)   │        │   (15%)   │
└─────┬─────┘        └─────┬─────┘           └─────┬─────┘        └─────┬─────┘
      │                    │                       │                    │
 7 Sub-KPIs           5 Sub-KPIs              10 Sub-KPIs          9 Sub-KPIs
```

### Dimension Breakdown & Weights

| Dimension | Default Weight | Description | Tracked KPIs |
| :--- | :---: | :--- | :--- |
| 🧠 **C – Computational Intelligence** | **25%** | Evaluates reasoning, planning capabilities, tool selection, and cognitive decision-making. | • Relevance Score<br>• Reasoning Quality<br>• Response Completeness<br>• Tool Selection Accuracy<br>• Planning Success Rate<br>• Task Decomposition Accuracy<br>• Recommendation Acceptance |
| 🎯 **A – Accuracy** | **30%** | Measures correctness of outputs, task execution success, precision, recall, and hallucination suppression. | • Task Success Rate<br>• Precision<br>• Recall<br>• Hallucination Rate *(Inverse)*<br>• Goal Completion Rate |
| 🛡️ **R – Reliability** | **30%** | Assesses operational consistency, execution safety, error recovery, compliance, and response latency. | • Failure Rate *(Inverse)*<br>• Retry Rate *(Inverse)*<br>• Tool Success Rate<br>• Latency (ms)<br>• Consistency Score<br>• Error Recovery Rate<br>• Safety Violation Rate *(Inverse)*<br>• Policy Compliance<br>• Audit Coverage<br>• PII Leakage Rate *(Inverse)* |
| 💰 **E – Economics** | **15%** | Analyzes financial ROI, token consumption efficiency, throughput, payback period, and productivity gains. | • Cost per Task ($)<br>• Token Consumption<br>• Throughput (tasks/hr)<br>• Resource Utilization<br>• Human Effort Saved<br>• Productivity Improvement<br>• Business ROI (%)<br>• Payback Period (months)<br>• Cost per Successful Task ($) |

### CARE Score Formula & Normalization

#### Overall Score Calculation
$$\text{CARE Score} = \frac{(C \times w_C) + (A \times w_A) + (R \times w_R) + (E \times w_E)}{w_C + w_A + w_R + w_E}$$

*Note: For partial evaluations where a dimension is omitted, weights are dynamically re-normalized across active dimensions.*

#### KPI Normalization Strategies
1. **Direct Percentage Metrics (0–100%)**: Passed through directly (e.g., Task Success Rate).
2. **Inverse Rate Metrics**: Converted using $S = 100 - \text{raw}$ (e.g., Failure Rate, Hallucination Rate, PII Leakage Rate).
3. **Linear Range Interpolation**: Scaled between an "Excellent" baseline ($S=100$) and a "Poor" baseline ($S=0$):
   - **Latency (ms)**: 200ms (Excellent → 100) to 10,000ms (Poor → 0)
   - **Cost per Task ($)**: $0.001 (Excellent → 100) to $1.00 (Poor → 0)
   - **Token Consumption**: 500 tokens (Excellent → 100) to 50,000 tokens (Poor → 0)
   - **Throughput**: 1,000 tasks/hr (Excellent → 100) to 1 task/hr (Poor → 0)
   - **Business ROI**: 500% ROI (Excellent → 100) to -100% ROI (Poor → 0)
   - **Payback Period**: 1 month (Excellent → 100) to 60 months (Poor → 0)

### Deployment Recommendation Tiers

| Score Range | Status | Recommendation Label | Action Guidance |
| :---: | :---: | :--- | :--- |
| **90.0 – 100.0** | 🟢 | **Production Ready** | Fully verified for enterprise production deployment. |
| **80.0 – 89.9** | 🔵 | **Pilot and Scale** | Ready for controlled user pilots and phased scaling. |
| **70.0 – 79.9** | 🟡 | **Needs Improvement** | Requires prompt engineering, fine-tuning, or architectural adjustments before deployment. |
| **< 70.0** | 🔴 | **Not Recommended** | Does not meet basic accuracy, safety, or economic thresholds. |

---

## ⚡ Automated AI-Agent Evaluation Pipeline

The platform supports **dual-mode evaluation**:
1. **Manual Evaluation**: Enter KPI measurements directly through a structured 6-step wizard.
2. **Automated Evaluation**: Ingest execution traces from AI agents, compute raw KPIs automatically, and route measurements into the existing CARE scoring and recommendation engines.

```
                     Automated Evaluation Pipeline
                     
┌──────────────┐     OTel / HTTP Traces     ┌────────────────────────┐
│   AI Agent   │ ─────────────────────────► │      Agent Traces      │
│  Execution   │                            │      Tool Traces       │
└──────────────┘                            └───────────┬────────────┘
                                                        │
                                                        ▼
┌────────────────────────────────────────────────────────────────────┐
│                       KPI Calculation Engine                       │
│    app/services/kpi_calculator.py (Raw values ONLY · No scoring)    │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Configured Evaluators                          │
│   • AccuracyEvaluator (Benchmark ground-truth test cases)          │
│   • ToolEvaluator     (Expected vs actual tool calls)              │
│   • SafetyEvaluator   (Architecture stub for safety guardrails)    │
│   • LLMJudge          (Architecture stub for LLM-as-a-Judge)       │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                    KpiMeasurement Records                          │
│   • Raw Value      • Unit       • Source       • Status            │
│   (Calculated from telemetry / benchmark OR marked unavailable)    │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │  Maps to EvaluationCreate
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Existing CARE Scoring Engine                    │
│   app/services/scoring.py (run_scoring — Reused without changes)   │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                Existing Recommendation Engine                      │
│   app/services/recommendations.py (generate_recommendations)       │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Evaluation Dashboard & Results                 │
│   • Overall CARE Score (0-100)        • Dimension Breakdown        │
│   • KPI Source Transparency Badges    • Coverage Indicator (%)     │
│   • Diagnostic Action Items           • PDF / CSV Exports          │
└────────────────────────────────────────────────────────────────────┘
```

### Pipeline Architecture

1. **Telemetry & Traces**: Captures task execution latency, status (`success` | `failed` | `error`), token usage (`input_tokens`, `output_tokens`, `total_tokens`), retry counts, and granular tool calls (`tool_name`, `latency_ms`, `status`).
2. **KPI Calculation Engine** (`app/services/kpi_calculator.py`): Pure functions that compute **raw** KPI metrics from aggregated trace data. **It never normalizes or calculates CARE scores.**
3. **Source Transparency & Never-Zero Rule**: If a KPI cannot be computed from available traces (e.g. reasoning quality requires an LLM judge), its status is recorded as `"unavailable"` and `raw_value = None`. **Unavailable metrics are never fabricated or treated as zero.**
4. **Pipeline Orchestrator** (`app/services/pipeline_orchestrator.py`): Bridges the calculated KPIs to the **existing** scoring engine (`run_scoring()`) and recommendation engine (`generate_recommendations()`), ensuring zero duplicate scoring logic.
5. **Asynchronous Execution**: Evaluation runs and KPI computations execute asynchronously via FastAPI `BackgroundTasks`. The frontend polls `GET /api/evaluation-runs/{id}/status` for non-blocking progress updates.

---

### KPI Source Classification & Transparency

The table below shows the source and automation status for each of the **31 CARE KPIs**:

| # | Dimension | KPI Name | Source | Automation Status | Why / Requirements |
|:-:|:---:|:---|:---:|:---:|:---|
| 1 | **R** | `latency_ms` | Telemetry | 🟢 **Automated** | Computed from trace duration (`sum(latency) / n_tasks`). |
| 2 | **R** | `failure_rate` | Telemetry | 🟢 **Automated** | Computed from trace status (`failed_tasks / total * 100`). |
| 3 | **R** | `retry_rate` | Telemetry | 🟢 **Automated** | Computed from `retry_count > 0` occurrences. |
| 4 | **R** | `tool_success_rate` | Telemetry | 🟢 **Automated** | Computed from `ToolTrace` status records. |
| 5 | **E** | `throughput` | Telemetry | 🟢 **Automated** | Computed from `completed_tasks / execution_hours`. |
| 6 | **E** | `token_consumption` | Telemetry | 🟢 **Automated** | Average `total_tokens` per completed task trace. |
| 7 | **E** | `cost_per_task` | Telemetry + Rates | 🟢 **Automated** | Derived from tokens + `LLM_INPUT/OUTPUT_COST_PER_1K_TOKENS`. |
| 8 | **E** | `cost_per_successful_task` | Telemetry + Rates | 🟢 **Automated** | Derived from tokens of successful tasks only. |
| 9 | **A** | `task_success_rate` | Benchmark | 🟢 **Phase 2** | Derived from `TestCaseResult` vs dataset `expected_output`. |
| 10 | **A** | `goal_completion_rate` | Benchmark | 🟢 **Phase 2** | Derived from test case score thresholding ($\ge 0.7$). |
| 11 | **C** | `tool_selection_accuracy` | Benchmark | 🟢 **Phase 2** | Evaluates `actual_tool` vs test case `expected_tool`. |
| 12 | **C** | `relevance_score` | LLM Judge | 🟡 *Unavailable* | Requires LLM-as-a-Judge (`LLM_JUDGE_PROVIDER`). |
| 13 | **C** | `reasoning_quality` | LLM Judge | 🟡 *Unavailable* | Requires LLM-as-a-Judge evaluation prompt. |
| 14 | **C** | `completeness` | LLM Judge | 🟡 *Unavailable* | Requires LLM-as-a-Judge evaluation prompt. |
| 15 | **C** | `planning_success_rate` | LLM Judge | 🟡 *Unavailable* | Requires multi-step plan trajectory evaluation. |
| 16 | **C** | `task_decomposition_accuracy` | LLM Judge | 🟡 *Unavailable* | Requires subtask decomposition evaluation. |
| 17 | **C** | `recommendation_acceptance_rate`| Business | 🟡 *Unavailable* | Requires human-in-the-loop reviewer logs. |
| 18 | **A** | `precision` | Benchmark Ground Truth | 🟡 *Unavailable* | Requires labeled binary classification dataset. |
| 19 | **A** | `recall` | Benchmark Ground Truth | 🟡 *Unavailable* | Requires labeled binary classification dataset. |
| 20 | **A** | `hallucination_rate` | LLM Judge | 🟡 *Unavailable* | Requires hallucination detection or judge model. |
| 21 | **R** | `consistency_score` | Evaluator | 🟡 *Unavailable* | Requires repeated runs across identical prompts. |
| 22 | **R** | `error_recovery_rate` | Business / Workflow | 🟡 *Unavailable* | Requires multi-turn recovery trajectory data. |
| 23 | **R** | `safety_violation_rate` | Safety Guardrail | 🟡 *Unavailable* | Requires safety service (Llama Guard / Azure Safety). |
| 24 | **R** | `policy_compliance_score` | Policy Evaluator | 🟡 *Unavailable* | Requires organizational policy compliance checker. |
| 25 | **R** | `audit_coverage` | Infrastructure | 🟡 *Unavailable* | Requires audit log coverage verification. |
| 26 | **R** | `pii_leakage_rate` | PII Detector | 🟡 *Unavailable* | Requires PII scanner (Presidio / AWS Comprehend). |
| 27 | **E** | `resource_utilization` | Infrastructure | 🟡 *Unavailable* | Requires CPU/GPU infrastructure metrics. |
| 28 | **E** | `human_effort_saved` | Business Data | 🟡 *Unavailable* | Requires baseline human time vs agent execution. |
| 29 | **E** | `productivity_improvement` | Business Data | 🟡 *Unavailable* | Requires business productivity measurement. |
| 30 | **E** | `business_roi` | Business Data | 🟡 *Unavailable* | Requires total financial cost and value attribution. |
| 31 | **E** | `payback_period_months` | Business Data | 🟡 *Unavailable* | Requires capital investment amortization data. |

> [!IMPORTANT]
> **Why Telemetry Alone Cannot Calculate All 31 KPIs**:
> Telemetry (spans, tokens, latency, status codes) accurately captures **operational performance** (e.g. latency, failure rates, tool call health, token consumption). However, evaluating semantic correctness (reasoning quality, hallucination rate) requires an **LLM Judge**, benchmark correctness requires **ground-truth datasets**, and business impact (ROI, human effort saved) requires **enterprise business data**. The CARE platform explicitly tracks and displays the origin of every metric.

---

### Evaluator Abstraction Architecture

All non-telemetry evaluators inherit from `BaseEvaluator` (`app/services/evaluators/base_evaluator.py`):

```python
class BaseEvaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(self, run, traces, tool_traces, test_case_results) -> List[RawKpiResult]: ...

    def is_available(self) -> bool: ...
```

- `AccuracyEvaluator` (`accuracy_evaluator.py`): Active. Computes `task_success_rate` and `goal_completion_rate` from benchmark results.
- `ToolEvaluator` (`tool_evaluator.py`): Active. Computes `tool_selection_accuracy` from expected vs actual tool calls.
- `SafetyEvaluator` (`safety_evaluator.py`): Documented architecture stub. Returns `unavailable` status until a guardrail provider is configured.
- `LlmJudge` (`llm_judge.py`): Documented architecture stub. Activates when `LLM_JUDGE_PROVIDER` is set (`openai` | `gemini` | `anthropic`).

---

### Ingesting Traces from Real Agents

Real AI agents stream their execution traces directly to the platform via REST endpoints:

```bash
# 1. Create an Evaluation Run
POST /api/evaluation-runs/
{
  "agent_name": "Production Customer Support Agent",
  "agent_type": "Customer Support",
  "total_tasks": 100,
  "llm_input_cost_per_1k": 0.0005,
  "llm_output_cost_per_1k": 0.0015
}
# Returns { "id": 42, "status": "PENDING" }

# 2. Ingest Agent Execution Traces (Bulk)
POST /api/evaluation-runs/42/traces
{
  "traces": [
    {
      "trace_id": "otel-span-001",
      "task_id": "task-user-1234",
      "model_name": "gpt-4o",
      "latency_ms": 642.5,
      "status": "success",
      "input_tokens": 520,
      "output_tokens": 210,
      "total_tokens": 730,
      "retry_count": 0
    }
  ]
}

# 3. Ingest Tool Call Traces
POST /api/evaluation-runs/42/tool-traces
{
  "agent_trace_id": 101,
  "tool_traces": [
    {
      "tool_name": "query_database",
      "latency_ms": 85.0,
      "status": "success"
    }
  ]
}

# 4. Generate CARE Score & Evaluation
POST /api/evaluation-runs/42/generate-evaluation
# Returns { "run_id": 42, "poll_url": "/api/evaluation-runs/42/status" }
```

---

### Simulation Adapter (Demo Mode)

For demonstration, development, and testing purposes without an external agent, the platform includes a **Simulation Adapter** (`app/routes/sample_agent.py`):

- **Adapter, Not Truth**: Generates synthetic traces using configurable parameters (task count, success rate, latency distribution, tool call frequency).
- **Explicit Labeling**: All generated traces carry `raw_metadata.simulation = True` and descriptions are prefixed with `[SIMULATION]`.
- **Identical Pipeline**: Executes the exact same pipeline orchestrator and scoring engine that real agent runs use.
- Accessible via the **Automated Evaluation** tab in the UI or `POST /api/simulation/run`.

---

### Secret Protection & Telemetry Exporters

- **Secret Protection**: All API keys and credentials are read exclusively from environment variables (`.env`). `.env` is listed in `.gitignore` and must never be committed.
- **Arize Telemetry**: Existing Arize Phoenix credentials (`ARIZE_SPACE_ID`, `ARIZE_API_KEY`, `ARIZE_PROJECT_NAME`) are preserved.
- **Configurable Exporter (`OTEL_EXPORTER_TYPE`)**:
  - `arize`: Export traces to Arize Phoenix (default).
  - `console`: Print spans to stdout for local debugging.
  - `otlp`: Export via gRPC to any OpenTelemetry collector (e.g. Jaeger, Grafana Tempo) via `OTEL_EXPORTER_OTLP_ENDPOINT`.

---

## ✨ Key Features

- 📊 **Interactive Executive Dashboard**: High-level KPI summaries, interactive score gauges, dimension distribution breakdown, top-performing agents list, and quick-action shortcuts.
- ➕ **Comprehensive Form Engine**: Structured metric entry grouped into 4 expandable dimension accordions with real-time field validation, range helpers, and instant score previews.
- 📈 **Results & Visual Analytics**: Radial radar charts comparing dimension scores, metric heatmaps, and automated diagnostic summaries.
- 💡 **Automated Diagnostic Recommendation Engine**: Rule-based system that analyzes low KPI values to output categorized strengths, weaknesses, and actionable remediation steps with severity levels (*Critical*, *High*, *Medium*, *Low*).
- 🆚 **Side-by-Side Agent Comparison**: Multi-agent comparison table highlighting overall winners, dimension winners, and granular KPI matrices across 2 or more evaluated agents.
- 📊 **Historical Trends & Analytics**: Time-series progression charts tracking agent evolution over time, distribution score buckets (0–59, 60–69, 70–79, 80–89, 90–100), and filtering by agent type.
- ⚙️ **Custom Weight Configuration Engine**: Dynamic configuration tool allowing administrators to alter CARE dimension weights (e.g. increase Reliability weight for healthcare applications or Economics for high-volume customer service).
- 📑 **Report Generation & Data Export**:
  - Download formal, formatted PDF evaluation certificates powered by ReportLab / HTML canvas fallback.
  - Export full evaluation datasets in standard CSV format for external analysis in Excel or BI tools.
- 🔄 **Evaluation Lifecycle Operations**: Single-click clone/duplicate, edit existing evaluation parameters, delete evaluations, and reset/seed mock enterprise evaluation data.

---

## 🛠️ System Architecture & Technology Stack

```
                                  Architecture Diagram
                                  
     ┌──────────────────────────────────────────────────────────────────────────┐
     │                      React 19 + TypeScript Frontend                      │
     │   (Vite, Tailwind CSS, Lucide Icons, Recharts, React Router v7)          │
     └────────────────────────────────────┬─────────────────────────────────────┘
                                          │  HTTP / REST API (JSON)
                                          ▼
     ┌──────────────────────────────────────────────────────────────────────────┐
     │                         FastAPI Python Backend                           │
     │  ┌───────────────────────┬───────────────────────┬────────────────────┐  │
     │  │   Scoring Engine      │ Recommendation Engine │ PDF Report Service │  │
     │  └───────────────────────┴───────────────────────┴────────────────────┘  │
     └────────────────────────────────────┬─────────────────────────────────────┘
                                          │  SQLAlchemy ORM 2.0
                                          ▼
     ┌──────────────────────────────────────────────────────────────────────────┐
     │                     SQLite Database (care_evaluator.db)                  │
     │                • evaluations      • weight_configs                       │
     └──────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Summary

#### Frontend Framework & Libraries
- **Core**: React 19, TypeScript 5.x, Vite 8
- **Styling & UI**: Tailwind CSS 3.4, Headless UI, Lucide React Icons, React Toastify
- **Data Visualization**: Recharts 3.x (Radar Charts, Line Charts, Bar Charts, Gauges)
- **Forms & State**: React Hook Form, Axios, React Router v7
- **Export Tools**: jsPDF, html2canvas

#### Backend Framework & Libraries
- **API Framework**: FastAPI 0.111.0, Uvicorn 0.30.1
- **Database & ORM**: SQLAlchemy 2.0.30, SQLite (`care_evaluator.db`), Alembic
- **Validation**: Pydantic v2.7.3, Pydantic-Settings
- **Document Generation**: ReportLab 4.2.2 (PDF generation), Python CSV Module

---

## 📂 Project Directory Structure

```
CARE Evaluation Platform/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── config/
│   │   │   └── settings.py         # App configuration & environment variables
│   │   ├── database/
│   │   │   └── database.py         # SQLAlchemy engine, session & Base
│   │   ├── models/
│   │   │   └── evaluation.py       # Evaluation & WeightConfig ORM schemas
│   │   ├── routes/
│   │   │   ├── analytics.py        # Trend analysis & aggregate endpoints
│   │   │   ├── comparison.py       # Multi-agent comparison endpoints
│   │   │   ├── config.py           # Weight configuration endpoints
│   │   │   ├── evaluations.py      # Main Evaluation CRUD & duplication
│   │   │   ├── reports.py          # PDF report download endpoint
│   │   │   └── utils.py            # Seed data & CSV export endpoints
│   │   ├── schemas/
│   │   │   └── evaluation.py       # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── pdf_report.py       # ReportLab PDF generator service
│   │   │   ├── recommendations.py # Rule-based diagnostic engine
│   │   │   └── scoring.py          # KPI normalization & CARE scoring logic
│   │   └── utils/
│   │       └── seed_data.py        # Auto-seeding mock evaluations
│   ├── .env                        # Local environment variables
│   ├── .env.example                # Example environment configuration
│   ├── care_evaluator.db           # SQLite database storage file
│   ├── main.py                     # FastAPI entry point & middleware
│   └── requirements.txt            # Python dependencies manifest
│
└── frontend/                       # React + Vite Frontend Application
    ├── public/                     # Static web assets
    ├── src/
    │   ├── assets/                 # SVGs and logos
    │   ├── components/             # Reusable UI components
    │   │   ├── CAREScoreGauge.tsx  # Radial score gauge meter
    │   │   ├── DimensionCard.tsx   # C, A, R, E dimension card
    │   │   ├── KPIInput.tsx        # Styled numerical input with limits
    │   │   ├── LoadingSkeleton.tsx # Shimmer loading state placeholder
    │   │   ├── RadarChart.tsx      # Recharts multi-dimension radar
    │   │   └── RecommendationCard.tsx # Diagnostic recommendation card
    │   ├── layouts/
    │   │   └── AppLayout.tsx       # Main layout with header & sidebar navigation
    │   ├── pages/
    │   │   ├── Analytics.tsx       # Performance distribution & trend view
    │   │   ├── Comparison.tsx      # Side-by-side agent comparison view
    │   │   ├── Dashboard.tsx       # Executive metrics overview dashboard
    │   │   ├── EvaluationResults.tsx # Single evaluation deep-dive view
    │   │   ├── History.tsx         # Full evaluation records table & search
    │   │   ├── NewEvaluation.tsx   # Evaluation creation & edit form
    │   │   └── Settings.tsx        # Dimension weight configuration view
    │   ├── services/
    │   │   └── api.ts              # Axios API service layer
    │   ├── types/
    │   │   └── index.ts            # TypeScript interfaces & types
    │   ├── utils/                  # Formatting & calculation utilities
    │   ├── App.tsx                 # React Router entry point
    │   ├── main.tsx                # React DOM render entry
    │   └── index.css               # Global Tailwind CSS styles
    ├── package.json                # Frontend NPM dependencies manifest
    ├── tailwind.config.js          # Tailwind CSS theme configuration
    └── vite.config.ts              # Vite dev server & proxy settings
```

---

## ⚡ Installation & Local Setup Guide

### Prerequisites

Ensure you have the following installed on your machine:
- **Python**: `v3.10` or higher
- **Node.js**: `v18.0` or higher (NPM included)
- **Git**

---

### 1. Backend Setup (FastAPI)

Navigate to the `backend` directory:

```bash
cd "CARE Evaluation Platform/backend"
```

#### Create & Activate Virtual Environment
- **On Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **On macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

#### Install Backend Dependencies
```bash
pip install -r requirements.txt
```

#### Launch Backend Server
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*The FastAPI server starts at `http://127.0.0.1:8000`. Database tables and initial sample data are automatically initialized on startup.*

---

### 2. Frontend Setup (React + Vite)

Open a new terminal window and navigate to the `frontend` directory:

```bash
cd "CARE Evaluation Platform/frontend"
```

#### Install Frontend Dependencies
```bash
npm install
```

#### Start Vite Development Server
```bash
npm run dev
```
*The React application will be available at `http://localhost:5173`. Requests to `/api` are automatically proxied to `http://127.0.0.1:8000` via `vite.config.ts`.*

---

## 📡 API Documentation Reference

The backend exposes interactive swagger documentation at `http://127.0.0.1:8000/docs` or ReDoc at `http://127.0.0.1:8000/redoc`.

### Summary of REST API Endpoints

| Category | HTTP Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **Evaluations** | `GET` | `/api/evaluations/` | List all evaluations (supports `search`, `agent_type`, `recommendation`, sorting, and pagination). |
| | `POST` | `/api/evaluations/` | Create a new evaluation and calculate scores. |
| | `GET` | `/api/evaluations/{id}` | Fetch full details for a specific evaluation. |
| | `PUT` | `/api/evaluations/{id}` | Update an existing evaluation record and re-score. |
| | `DELETE` | `/api/evaluations/{id}` | Delete an evaluation by ID. |
| | `POST` | `/api/evaluations/{id}/duplicate` | Clone an existing evaluation. |
| **Comparison** | `POST` | `/api/comparison/` | Perform side-by-side comparison across multiple evaluation IDs. |
| **Analytics** | `GET` | `/api/analytics/summary` | Retrieve global aggregated metrics, trends, and score distribution. |
| **Configuration** | `GET` | `/api/config/weights` | Get current CARE dimension weight configuration. |
| | `PUT` | `/api/config/weights` | Update CARE dimension weight configuration. |
| **Reports** | `GET` | `/api/reports/{id}/pdf` | Generate and download a PDF report for an evaluation. |
| **Utilities** | `POST` | `/api/utils/seed` | Seed or reset sample evaluations in SQLite DB. |
| | `GET` | `/api/utils/export/csv` | Download complete dataset as a CSV file. |
| **System** | `GET` | `/health` | Health check endpoint. |

---

## 🗄️ Database Schema & Data Models

The platform uses SQLite managed via SQLAlchemy ORM models defined in [backend/app/models/evaluation.py](file:///c:/CARE%20Evaluation%20Platform/backend/app/models/evaluation.py).

### Core Tables

#### 1. `evaluations` Table
Stores basic metadata, raw KPI values, snapshot weights, computed dimension scores, final CARE score, and diagnostic JSON structures.

- **Primary Keys & Metadata**: `id`, `agent_name`, `agent_type`, `description`, `evaluator`, `created_at`, `updated_at`
- **Snapshot Weights**: `weight_c`, `weight_a`, `weight_r`, `weight_e`
- **Computed Dimension Scores**: `score_c`, `score_a`, `score_r`, `score_e`, `care_score`, `recommendation`
- **Raw Metric Fields**: 31 KPI columns corresponding to C, A, R, and E dimensions.
- **JSON Payload Fields**:
  - `strengths`: List of identified agent strengths.
  - `weaknesses`: List of identified agent weaknesses.
  - `recommendations`: Array of structured diagnostic recommendation objects.
  - `kpi_scores`: Dictionary of 0–100 normalized scores for every individual KPI.

#### 2. `weight_configs` Table
Stores active application-wide CARE dimension weights.
- `id` (Primary Key, fixed to 1 for single-active config)
- `weight_c` (default: 0.25)
- `weight_a` (default: 0.30)
- `weight_r` (default: 0.30)
- `weight_e` (default: 0.15)
- `updated_at`

---

## 💡 Automated Recommendation Engine

The platform includes a rule-based engine ([backend/app/services/recommendations.py](file:///c:/CARE%20Evaluation%20Platform/backend/app/services/recommendations.py)) that inspects normalized scores and triggers specific improvement suggestions:

- **Reasoning Quality (< 60)** 🚨 *Critical*: Suggests adopting Chain-of-Thought (CoT), ReAct frameworks, or upgrading the underlying foundation LLM.
- **Tool Selection Accuracy (< 60)** ⚠️ *High*: Suggests improving tool descriptions, introducing tool routing validation, or fine-tuning tool usage prompts.
- **Planning Success Rate (< 60)** ⚠️ *High*: Recommends implementing hierarchical task decomposition modules.
- **Hallucination Rate (> 15%)** 🚨 *Critical*: Directs implementation of RAG grounding, vector search distance thresholds, or facts verification guards.
- **Failure Rate (> 10%)** 🚨 *Critical*: Advises implementing retry policies, fallback LLMs, and exponential backoff mechanisms.
- **Safety Violation Rate (> 1%)** 🚨 *Critical*: Requires immediate guardrail enforcement (NeMo Guardrails, Llama Guard) and policy prompt checks.
- **Latency (> 5,000ms)** 🟡 *Medium*: Suggests prompt compression, streaming responses, speculative decoding, or model quantization.
- **Cost per Task (> $0.50)** 🟡 *Medium*: Recommends prompt token optimization, semantic caching, or routing simple tasks to smaller models (e.g. GPT-4o-mini, Haiku).

---

## 📑 Reporting & Data Export

### 1. Executive PDF Reports
Generated dynamically via ReportLab on the backend or using `html2canvas` + `jsPDF` in the frontend fallback mode. PDF reports feature:
- Official CARE Evaluation Certificate header with badge styling.
- Executive summary with overall score gauge & deployment status.
- Dimension score breakdown table with metric radar charts.
- Detailed strength & weakness list.
- Prioritized remediation recommendations table.

### 2. CSV Data Export
Instant streaming CSV generation containing all raw KPI values, scores, timestamps, and model parameters for offline analysis or compliance logging.

---

## 🧪 Development & Testing

### Running Backend Tests
```bash
cd backend
pytest
```

### Running Frontend Linter & Build Check
```bash
cd frontend
npm run lint
npm run build
```

---

## 📄 License & Attribution

Developed for enterprise AI benchmarking and governance. Built with React, Vite, FastAPI, and SQLAlchemy.
