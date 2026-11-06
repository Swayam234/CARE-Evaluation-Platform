"""
CARE Housing Society – Application Configuration (v2)
Extends existing CARE Evaluator settings with full housing complaint agent config.
"""
from pydantic_settings import BaseSettings
from typing import List, Literal
import os


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────────────────────────
    app_name: str = "CARE Housing Society"
    app_version: str = "2.0.0"
    app_env: str = "development"

    # ─── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./care_housing.db"

    # ─── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:4173"

    # ─── JWT Auth ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production-use-32-char-minimum-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ─── AI Provider ──────────────────────────────────────────────────────────
    ai_provider: Literal["gemini", "openai", "claude", "demo"] = "demo"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro-latest"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""

    # ─── Feature Flags ────────────────────────────────────────────────────────
    vector_search_enabled: bool = False
    redis_cache_enabled: bool = False
    background_jobs_enabled: bool = True
    email_notifications_enabled: bool = False
    sms_notifications_enabled: bool = False
    whatsapp_notifications_enabled: bool = False

    # ─── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ─── File Upload ──────────────────────────────────────────────────────────
    upload_dir: str = "uploads"
    max_file_size_mb: int = 50

    # ─── Rate Limiting ────────────────────────────────────────────────────────
    chat_rate_limit: str = "30/minute"
    api_rate_limit: str = "100/minute"

    # ─── Arize Telemetry (existing – credentials preserved from .env) ────────
    arize_space_id: str = ""
    arize_api_key: str = ""
    arize_project_name: str = "CARE-Housing"

    # ─── Automated Evaluation Pipeline ────────────────────────────────────────
    # Token cost rates for cost_per_task / cost_per_successful_task calculation.
    # Leave empty ("") to mark those KPIs as "unavailable" rather than fabricating values.
    llm_input_cost_per_1k_tokens: float = 0.0   # 0.0 = not configured
    llm_output_cost_per_1k_tokens: float = 0.0  # 0.0 = not configured

    # LLM-as-a-Judge configuration (optional).
    # Set to enable reasoning / hallucination / quality KPIs.
    # Provider must be one of: openai | gemini | anthropic | (blank = disabled)
    # API keys are already configured above – do NOT add duplicate key fields.
    llm_judge_provider: str = ""    # blank = LLM judge disabled
    llm_judge_model: str = ""       # e.g. gpt-4o, gemini-1.5-pro, claude-3-5-sonnet

    # OpenTelemetry exporter type.
    # arize   – use existing Arize Phoenix integration (default)
    # console – print spans to stdout (development/debugging)
    # otlp    – send to any OTLP-compatible collector (Jaeger, Tempo, etc.)
    otel_exporter_type: str = "arize"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    @property
    def llm_input_cost_configured(self) -> bool:
        return self.llm_input_cost_per_1k_tokens > 0

    @property
    def llm_output_cost_configured(self) -> bool:
        return self.llm_output_cost_per_1k_tokens > 0

    @property
    def llm_judge_enabled(self) -> bool:
        return bool(self.llm_judge_provider.strip())

    # ─── Email ────────────────────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@carehousing.com"

    # ─── Society ──────────────────────────────────────────────────────────────
    default_city_code: str = "MUM"
    default_society_name: str = "Sunrise Heights Society"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def upload_path(self) -> str:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.upload_dir)
        os.makedirs(path, exist_ok=True)
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
