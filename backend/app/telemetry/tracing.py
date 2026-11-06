"""
Telemetry / Tracing – Extended
================================
Extends the existing Arize Phoenix integration with:
  - Environment-variable-driven exporter configuration
  - A get_tracer() utility for use by pipeline modules
  - Graceful fallback when Arize credentials are not configured

EXISTING Arize registration is preserved exactly as-is.
New config is additive only – nothing is replaced.

Secret protection:
  - All credentials read from environment variables only
  - No hardcoded credentials anywhere in this file
  - .gitignore must include .env (enforced at project level)
"""
import os
import contextlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── DummyTracer fallback (used throughout the app) ───────────────────────────
class DummySpan:
    def set_attribute(self, *a, **kw): pass
    def set_status(self, *a, **kw): pass
    def record_exception(self, *a, **kw): pass
    def add_event(self, *a, **kw): pass


class DummyTracer:
    @contextlib.contextmanager
    def start_as_current_span(self, name, *args, **kwargs):
        yield DummySpan()


class _DummyStatus:
    pass


class _DummyStatusCode:
    ERROR = "ERROR"
    OK = "OK"


# ── Exporter type from environment ───────────────────────────────────────────
OTEL_EXPORTER_TYPE = os.getenv("OTEL_EXPORTER_TYPE", "arize").lower()

tracer_provider = None
_tracer_initialized = False


def _init_arize() -> bool:
    """Initialize Arize Phoenix tracer. Returns True on success."""
    try:
        from arize.otel import register
        from app.config.settings import settings

        if not settings.arize_space_id or not settings.arize_api_key:
            logger.warning(
                "Arize credentials not configured (ARIZE_SPACE_ID or ARIZE_API_KEY missing). "
                "Telemetry will use console exporter as fallback."
            )
            return False

        global tracer_provider
        tracer_provider = register(
            space_id=settings.arize_space_id,
            api_key=settings.arize_api_key,
            project_name=settings.arize_project_name,
            log_to_console=(os.getenv("APP_ENV", "development") == "development"),
        )
        logger.info("Arize Phoenix tracer registered successfully (project: %s)", settings.arize_project_name)
        return True
    except ImportError:
        logger.warning("arize-otel package not installed. Falling back to console/OTLP exporter.")
        return False
    except Exception as exc:
        logger.error("Arize registration failed: %s", exc)
        return False


def _init_console() -> bool:
    """Initialize OpenTelemetry console exporter."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        global tracer_provider
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        tracer_provider = provider
        logger.info("OpenTelemetry console exporter initialized.")
        return True
    except ImportError:
        logger.warning("opentelemetry-sdk not installed. Tracing disabled.")
        return False


def _init_otlp() -> bool:
    """Initialize OpenTelemetry OTLP exporter."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        global tracer_provider
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        tracer_provider = provider
        logger.info("OpenTelemetry OTLP exporter initialized (endpoint: %s).", endpoint)
        return True
    except ImportError:
        logger.warning("opentelemetry-exporter-otlp not installed. Tracing disabled.")
        return False


def initialize_telemetry() -> None:
    """
    Initialize telemetry based on OTEL_EXPORTER_TYPE environment variable.
    Called once at application startup.
    """
    global _tracer_initialized
    if _tracer_initialized:
        return

    exporter = OTEL_EXPORTER_TYPE
    logger.info("Initializing telemetry with exporter: %s", exporter)

    success = False
    if exporter == "arize":
        success = _init_arize()
        if not success:
            logger.info("Falling back to console exporter.")
            success = _init_console()
    elif exporter == "console":
        success = _init_console()
    elif exporter == "otlp":
        success = _init_otlp()
    else:
        logger.warning("Unknown OTEL_EXPORTER_TYPE '%s'. Falling back to console.", exporter)
        success = _init_console()

    _tracer_initialized = True
    if not success:
        logger.warning("All telemetry exporters failed. Tracing disabled.")


def get_tracer(name: str = "care_pipeline"):
    """
    Get an OpenTelemetry tracer by name.
    Returns a DummyTracer if OpenTelemetry is not available.
    """
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return DummyTracer()
    except Exception:
        return DummyTracer()


# ── Legacy compatibility: keep existing Arize print statements ───────────────
# The existing code in scoring.py and recommendations.py uses:
#   from opentelemetry import trace
#   tracer = trace.get_tracer(__name__)
# This continues to work unchanged.