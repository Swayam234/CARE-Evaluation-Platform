"""
CARE Evaluator – FastAPI Application Entry Point
=================================================
Starts the API server with CORS, route registration, auto DB creation,
and optional sample data seeding on first startup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.database.database import engine, Base, SessionLocal
from app.models import evaluation  # noqa – ensures models are registered before create_all
from app.routes import evaluations, comparison, analytics, config, utils, reports


# ── Create all DB tables on startup ──────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Auto-seed on first launch ─────────────────────────────────────────────────
from app.utils.seed_data import seed_database
with SessionLocal() as db:
    seed_database(db)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="CARE Evaluator API",
    description="""
## Enterprise Agentic AI Evaluation Platform

The **CARE framework** evaluates AI agents across four dimensions:

| Dimension | Weight | Description |
|---|---|---|
| 🧠 **C** – Computational Intelligence | 25% | Reasoning, planning, tool selection |
| 🎯 **A** – Accuracy | 30% | Task success, precision, recall, hallucinations |
| 🛡️ **R** – Reliability | 30% | Consistency, safety, compliance, latency |
| 💰 **E** – Economics | 15% | Cost, ROI, throughput, productivity |

**CARE Score = C×0.25 + A×0.30 + R×0.30 + E×0.15**
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(evaluations.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(utils.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "version": settings.app_version,
    }
