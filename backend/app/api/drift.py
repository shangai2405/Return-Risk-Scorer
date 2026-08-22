from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.db import get_db
from backend.app.services.drift import drift_service

router = APIRouter()

@router.get("/drift-status")
def get_drift_status(
    window_size: int = Query(200, description="Rolling window size for production comparison"),
    db: Session = Depends(get_db)
):
    """
    Read-only statistical drift monitoring endpoint.
    Runs Two-Sample KS test for numeric features (p < 0.05) and PSI for categorical features (PSI > 0.2).
    """
    return drift_service.compute_drift(db=db, window_size=window_size)
