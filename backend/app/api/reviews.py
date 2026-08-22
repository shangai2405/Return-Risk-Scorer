from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.db import get_db
from backend.app.models.schema import AnalystReviewInput, AgreementStats
from backend.app.services.agreement import submit_analyst_review, compute_agreement_stats

router = APIRouter()

@router.post("/orders/{order_id}/review")
def post_order_review(order_id: str, review_input: AnalystReviewInput, db: Session = Depends(get_db)):
    """
    Submits a human analyst review decision for an order.
    """
    review_input.order_id = order_id
    return submit_analyst_review(db=db, review_input=review_input)

@router.get("/agreement-stats", response_model=AgreementStats)
def get_agreement_stats(db: Session = Depends(get_db)):
    """
    Returns analyst-model agreement rates, overturn rates, and decision breakdown.
    """
    return compute_agreement_stats(db=db)
