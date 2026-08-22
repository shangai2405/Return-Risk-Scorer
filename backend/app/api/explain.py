import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.db import get_db, ScoredOrderRecord
from backend.app.models.schema import OrderInput
from backend.app.services.scoring import build_feature_vector
from backend.app.services.explain import explain_vector

router = APIRouter()

@router.get("/orders/{order_id}/explain")
def get_order_explanation(order_id: str, db: Session = Depends(get_db)):
    # Try finding by string order_id or integer record id
    record = None
    if order_id.isdigit():
        record = db.query(ScoredOrderRecord).filter(ScoredOrderRecord.id == int(order_id)).first()
    if not record:
        record = db.query(ScoredOrderRecord).filter(ScoredOrderRecord.order_id == order_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Order record not found in database")

    payload_dict = json.loads(record.order_payload_json)
    order_input = OrderInput(**payload_dict)

    vector_df = build_feature_vector(order_input)
    explain_res = explain_vector(vector_df, record.flag)

    return {
        "order_id": record.order_id,
        "risk_score": record.risk_score,
        "flag": record.flag,
        "recommended_action": record.recommended_action,
        "top_factors": explain_res["top_factors"],
        "factor_details": explain_res["factor_details"],
        "scored_at": record.scored_at.isoformat() if record.scored_at else ""
    }
