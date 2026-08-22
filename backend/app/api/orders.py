import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.db import get_db, ScoredOrderRecord
from backend.app.models.schema import OrderRecordResponse

router = APIRouter()

@router.get("/orders", response_model=List[OrderRecordResponse])
def get_orders(
    flag: Optional[str] = Query(None, description="Filter by flag status, e.g., high_risk"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(ScoredOrderRecord)

    if flag == "high_risk":
        query = query.filter(ScoredOrderRecord.flag == True)
    elif flag == "low_risk":
        query = query.filter(ScoredOrderRecord.flag == False)

    records = query.order_by(ScoredOrderRecord.id.desc()).offset(offset).limit(limit).all()

    result = []
    for r in records:
        result.append(OrderRecordResponse(
            id=r.id,
            order_id=r.order_id,
            order_payload=json.loads(r.order_payload_json),
            risk_score=r.risk_score,
            flag=r.flag,
            top_factors=json.loads(r.top_factors_json),
            recommended_action=r.recommended_action,
            scored_at=r.scored_at.isoformat() if r.scored_at else ""
        ))
    return result
