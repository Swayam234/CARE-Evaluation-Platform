"""
CARE Evaluator API Entry Point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config.settings import settings
from app.database.database import engine, Base, SessionLocal

# Import models so SQLAlchemy registers tables (new pipeline models are in pipeline.py)
from app.models import evaluation, pipeline  # noqa: F401

# Import CARE Evaluator routes
from app.routes import evaluations, comparison, analytics, config, utils, reports

# Import Automated Evaluation Pipeline routes
from app.routes import pipeline as pipeline_routes
from app.routes import datasets as datasets_routes
from app.routes import sample_agent as sample_agent_routes

# ── Create all DB tables ──────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── FastAPI Application ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="""
## CARE Evaluation Framework

**C**omputational Intelligence, **A**ccuracy, **R**eliability, **E**conomics — a comprehensive framework for scoring and comparing agentic AI systems.
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Uploads Mount ──────────────────────────────────────────────────────
uploads_dir = settings.upload_path
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ── CARE Evaluation Routers (existing – unchanged) ───────────────────────────
app.include_router(evaluations.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(utils.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# ── Automated Evaluation Pipeline Routers (new) ───────────────────────────────
app.include_router(pipeline_routes.router, prefix="/api")
app.include_router(datasets_routes.router, prefix="/api")
app.include_router(sample_agent_routes.router, prefix="/api")


# ── Health Check Endpoints ────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
        "ai_provider": settings.ai_provider,
    }


@app.get("/health/db", tags=["System"])
def db_health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"database": "connected", "status": "ok"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}


@app.get("/", tags=["System"])
def root():
    return {
        "message": f"Welcome to {settings.app_name} API v{settings.app_version}",
        "docs": "/docs",
        "version": settings.app_version,
    }
