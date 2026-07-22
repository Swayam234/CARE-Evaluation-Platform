"""
CARE Evaluator – Application Configuration
Reads settings from environment variables / .env file.
Structured so JWT auth can be added without major refactoring.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App metadata
    app_name: str = "CARE Evaluator"
    app_version: str = "1.0.0"
    app_env: str = "development"

    # Database
    database_url: str = "sqlite:///./care_evaluator.db"

    # CORS – comma-separated list of allowed origins
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ─── Auth scaffold ───────────────────────────────────────────────────────
    # Uncomment and populate when adding JWT auth in a future sprint.
    # jwt_secret_key: str = "change-me"
    # jwt_algorithm: str = "HS256"
    # jwt_access_token_expire_minutes: int = 30
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
