import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.models.schema import OrderInput, ScoreResponse
from backend.app.core.db import get_db, ScoredOrderRecord, ProductionFeaturesRecord
from backend.app.services.scoring import score_order
from backend.app.services.explain import explain_vector

router = APIRouter()

@router.post("/score", response_model=ScoreResponse)
def score_order_endpoint(order_input: OrderInput, db: Session = Depends(get_db)):
    score_res = score_order(order_input)
    explain_res = explain_vector(score_res["vector_df"], score_res["flag"])

    order_id_str = order_input.order_id or "ORD-DYNAMIC-1"

    # Persist audit record
    record = ScoredOrderRecord(
        order_id=order_id_str,
        order_payload_json=json.dumps(order_input.model_dump()),
        risk_score=score_res["risk_score"],
        flag=score_res["flag"],
        top_factors_json=json.dumps(explain_res["top_factors"]),
        recommended_action=explain_res["recommended_action"]
    )
    db.add(record)

    # Persist production feature vector for drift monitoring
    feat_dict = score_res["vector_df"].iloc[0].to_dict()
    feat_record = ProductionFeaturesRecord(
        order_id=order_id_str,
        features_json=json.dumps(feat_dict)
    )
    db.add(feat_record)

    db.commit()
    db.refresh(record)

    return ScoreResponse(
        order_id=order_id_str,
        risk_score=score_res["risk_score"],
        flag=score_res["flag"],
        threshold=score_res["threshold"],
        top_factors=explain_res["top_factors"],
        factor_details=explain_res["factor_details"],
        recommended_action=explain_res["recommended_action"]
    )
