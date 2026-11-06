"""
Recommendation Engine
=====================
Rule-based engine that generates actionable improvement suggestions
based on dimension scores and specific KPI values.

Each recommendation has:
  - dimension: which CARE dimension it relates to
  - severity: critical | high | medium | low
  - title: short label
  - description: actionable explanation
  - kpi: the specific KPI driving the recommendation (if any)
"""
from typing import List, Dict, Any, Optional
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    tracer = trace.get_tracer(__name__)
except ImportError:
    import contextlib
    class DummySpan:
        def set_attribute(self, *a, **kw): pass
        def set_status(self, *a, **kw): pass
        def record_exception(self, *a, **kw): pass
        def add_event(self, *a, **kw): pass
    class DummyTracer:
        @contextlib.contextmanager
        def start_as_current_span(self, name, *args, **kwargs):
            yield DummySpan()
    tracer = DummyTracer()
    class Status:
        def __init__(self, *a, **kw): pass
    class StatusCode:
        ERROR = "ERROR"
        OK = "OK"



def _rec(dimension: str, severity: str, title: str, description: str, kpi: str = "") -> Dict[str, Any]:
    return {"dimension": dimension, "severity": severity, "title": title, "description": description, "kpi": kpi}


def generate_recommendations(
    score_c: Optional[float],
    score_a: Optional[float],
    score_r: Optional[float],
    score_e: Optional[float],
    kpi_scores: Dict[str, float],
) -> tuple[List[str], List[str], List[Dict[str, Any]]]:

    with tracer.start_as_current_span("generate_recommendations") as span:

        try:

            span.add_event("Generating recommendations")

            strengths: List[str] = []
            weaknesses: List[str] = []
            recs: List[Dict[str, Any]] = []

    
    
    # ── Identify Strengths ────────────────────────────────────────────────────
            if score_c is not None and score_c >= 80:
              strengths.append(f"Strong Computational Intelligence ({score_c:.1f}/100)")
            if score_a is not None and score_a >= 80:
              strengths.append(f"High Accuracy performance ({score_a:.1f}/100)")
            if score_r is not None and score_r >= 80:
              strengths.append(f"Excellent Reliability ({score_r:.1f}/100)")
            if score_e is not None and score_e >= 80:
              strengths.append(f"Strong Economic Value ({score_e:.1f}/100)")

    # ── Computational Intelligence Recommendations ────────────────────────────
            if score_c is not None and score_c < 70:
              weaknesses.append(f"Weak Computational Intelligence ({score_c:.1f}/100)")

            if kpi_scores.get("reasoning_quality", 100) < 60:
              recs.append(_rec("C", "critical", "Enhance Reasoning Strategy",
            "The agent's reasoning quality is poor. Consider using chain-of-thought prompting, "
            "structured reasoning frameworks (ReAct, CoT), or switching to a more capable foundation model.",
            "reasoning_quality"))

            if kpi_scores.get("tool_selection_accuracy", 100) < 60:
              recs.append(_rec("C", "high", "Improve Tool Selection Logic",
            "Tool selection accuracy is low. Review tool descriptions for clarity, add tool selection "
            "validation steps, and consider fine-tuning the agent on tool routing examples.",
            "tool_selection_accuracy"))

            if kpi_scores.get("planning_success_rate", 100) < 60:
              recs.append(_rec("C", "high", "Strengthen Planning Capabilities",
            "The agent struggles with multi-step planning. Implement a dedicated planning module, "
            "use hierarchical task decomposition, or integrate a planning-specific LLM.",
            "planning_success_rate"))

            if kpi_scores.get("task_decomposition_accuracy", 100) < 70:
              recs.append(_rec("C", "medium", "Refine Task Decomposition",
            "Tasks are not being broken down effectively. Add examples of proper decomposition "
            "to the system prompt and implement subtask validation checkpoints.",
            "task_decomposition_accuracy"))

            if kpi_scores.get("relevance_score", 100) < 70:
              recs.append(_rec("C", "medium", "Improve Response Relevance",
            "Responses are not sufficiently relevant to the user's intent. "
            "Enhance the retrieval pipeline, improve context injection, and tune the system prompt.",
            "relevance_score"))

    # ── Accuracy Recommendations ──────────────────────────────────────────────
            if score_a is not None and score_a < 70:
              weaknesses.append(f"Low Accuracy ({score_a:.1f}/100)")

            if kpi_scores.get("hallucination_rate", 100) < 60:
              recs.append(_rec("A", "critical", "Reduce Hallucinations",
            "The agent is producing significant hallucinations. Implement RAG with verified sources, "
            "add factual grounding checks, use lower temperature settings, and deploy a hallucination "
            "detection guardrail before responses reach the user.",
            "hallucination_rate"))

            if kpi_scores.get("task_success_rate", 100) < 70:
              recs.append(_rec("A", "high", "Increase Task Success Rate",
            "Too many tasks are failing. Analyse failure patterns, improve the system prompt with "
            "clearer instructions, add retry-with-feedback loops, and create a task-specific fine-tune.",
            "task_success_rate"))

            if kpi_scores.get("precision", 100) < 70:
              recs.append(_rec("A", "high", "Improve Output Precision",
            "Precision is below target. Add output format constraints, implement output parsing "
            "validators, and use structured output modes where the model supports them.",
            "precision"))

            if kpi_scores.get("recall", 100) < 70:
              recs.append(_rec("A", "medium", "Improve Recall",
            "The agent misses relevant information. Expand retrieval coverage, increase the number "
            "of retrieved chunks, and use hybrid search (dense + sparse) in the RAG pipeline.",
            "recall"))

            if kpi_scores.get("goal_completion_rate", 100) < 75:
              recs.append(_rec("A", "medium", "Improve Goal Completion",
            "Goals are not consistently completed. Add explicit goal-tracking logic, implement "
            "progress monitoring checkpoints, and use outcome-based prompting.",
            "goal_completion_rate"))

    # ── Reliability Recommendations ───────────────────────────────────────────
            if score_r is not None and score_r < 70:
              weaknesses.append(f"Reliability Concerns ({score_r:.1f}/100)")

            if kpi_scores.get("failure_rate", 100) < 60:
              recs.append(_rec("R", "critical", "Reduce Failure Rate",
            "The agent fails too frequently. Add circuit breakers, implement graceful degradation, "
            "improve error handling, and establish automated alerting for failure spikes.",
            "failure_rate"))

            if kpi_scores.get("safety_violation_rate", 100) < 70:
              recs.append(_rec("R", "critical", "Deploy Safety Guardrails",
            "Safety violations are occurring. Integrate a content moderation layer (e.g., Llama Guard), "
            "define explicit prohibited outputs in the system prompt, and establish a human review "
            "queue for flagged responses.",
            "safety_violation_rate"))

            if kpi_scores.get("pii_leakage_rate", 100) < 70:
              recs.append(_rec("R", "critical", "Prevent PII Leakage",
            "PII is being leaked in responses. Deploy a PII detection and redaction service, "
            "restrict the context available to the agent, and audit all data flows for PII exposure.",
            "pii_leakage_rate"))

            if kpi_scores.get("policy_compliance_score", 100) < 75:
              recs.append(_rec("R", "high", "Improve Policy Compliance",
            "The agent is not consistently complying with policies. Codify policies as explicit "
            "rules in the system prompt, add a policy-checking pre-response hook, and conduct "
            "regular compliance audits.",
            "policy_compliance_score"))

            if kpi_scores.get("consistency_score", 100) < 70:
              recs.append(_rec("R", "high", "Improve Response Consistency",
            "Responses vary significantly for similar inputs. Reduce temperature, implement response "
            "caching for common queries, and add a consistency testing suite to CI/CD.",
            "consistency_score"))

            if kpi_scores.get("latency_ms", 100) < 60:
              recs.append(_rec("R", "medium", "Reduce Response Latency",
            "Response latency is high. Consider using a faster model tier, implement streaming "
            "responses, add a semantic cache layer, and move to edge inference where possible.",
            "latency_ms"))

            if kpi_scores.get("audit_coverage", 100) < 70:
              recs.append(_rec("R", "medium", "Expand Audit Coverage",
            "Insufficient audit coverage creates compliance risk. Implement comprehensive logging "
            "of all agent actions, integrate with an observability platform, and define audit retention policies.",
            "audit_coverage"))

    # ── Economics Recommendations ─────────────────────────────────────────────
            if score_e is not None and score_e < 70:
              weaknesses.append(f"Poor Economic Value ({score_e:.1f}/100)")

            if kpi_scores.get("token_consumption", 100) < 60:
              recs.append(_rec("E", "high", "Reduce Token Consumption",
            "Token usage is too high, driving up costs. Implement prompt compression, use smaller "
            "context windows, cache common sub-tasks, and consider switching to a more efficient model.",
            "token_consumption"))

            if kpi_scores.get("cost_per_task", 100) < 60:
              recs.append(_rec("E", "high", "Optimise Cost per Task",
            "Cost per task is excessive. Use model routing (route simple tasks to cheaper models), "
            "implement prompt caching, batch similar requests, and optimise inference infrastructure.",
            "cost_per_task"))

            if kpi_scores.get("business_roi", 100) < 60:
              recs.append(_rec("E", "medium", "Improve Business ROI",
            "ROI is below expectations. Identify and prioritise the highest-value use cases, "
            "reduce manual overhead in the workflow, and measure productivity gains more rigorously.",
            "business_roi"))

            if kpi_scores.get("throughput", 100) < 60:
              recs.append(_rec("E", "medium", "Increase Throughput",
            "Throughput is low. Scale the inference infrastructure horizontally, implement "
            "async processing for non-real-time tasks, and use batching to maximise GPU utilisation.",
            "throughput"))

            if kpi_scores.get("human_effort_saved", 100) < 60:
              recs.append(_rec("E", "low", "Maximise Human Effort Savings",
            "The agent is not saving as much human time as expected. Automate more of the workflow, "
            "expand the agent's scope of autonomous action, and reduce unnecessary human-in-the-loop steps.",
            "human_effort_saved"))

    # Sort: critical first, then high, medium, low
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            recs.sort(key=lambda r: severity_order.get(r["severity"], 99))

            span.set_attribute("recommendations.count", len(recs))
            span.set_attribute("strengths.count", len(strengths))
            span.set_attribute("weaknesses.count", len(weaknesses))

            span.add_event("Recommendations generated")

            span.set_status(Status(StatusCode.OK))

            return strengths, weaknesses, recs


        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            raise
