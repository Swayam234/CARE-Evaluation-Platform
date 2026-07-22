"""
Configuration API Routes
========================
Manage dimension weights + auth scaffold endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.evaluation import WeightConfig
from app.schemas.evaluation import WeightConfigBase, WeightConfigRead, TokenResponse

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("/weights", response_model=WeightConfigRead)
def get_weights(db: Session = Depends(get_db)):
    """Get the current active dimension weight configuration."""
    config = db.query(WeightConfig).filter(WeightConfig.id == 1).first()
    if not config:
        config = WeightConfig(id=1, weight_c=0.25, weight_a=0.30, weight_r=0.30, weight_e=0.15)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("/weights", response_model=WeightConfigRead)
def update_weights(data: WeightConfigBase, db: Session = Depends(get_db)):
    """Update the active dimension weight configuration."""
    config = db.query(WeightConfig).filter(WeightConfig.id == 1).first()
    if not config:
        config = WeightConfig(id=1)
        db.add(config)

    config.weight_c = data.weight_c
    config.weight_a = data.weight_a
    config.weight_r = data.weight_r
    config.weight_e = data.weight_e
    db.commit()
    db.refresh(config)
    return config


# ─── Auth Scaffold ────────────────────────────────────────────────────────────
# These endpoints are stubs. Replace with real JWT implementation in a future sprint.

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth Scaffold"])
def login_stub(username: str, password: str):
    """
    Auth scaffold endpoint.
    Returns a placeholder response. Replace with real JWT logic when implementing auth.
    """
    return TokenResponse(
        message="Auth scaffold active – JWT not yet implemented. Any credentials accepted in dev mode.",
        user=None,
        access_token=None,
    )


@router.get("/auth/me", response_model=TokenResponse, tags=["Auth Scaffold"])
def me_stub():
    """Returns current user info scaffold."""
    return TokenResponse(message="Auth scaffold – user context not yet implemented.")
