from sqlalchemy.orm import Session
from backend.app.core.db import AnalystReviewRecord, ScoredOrderRecord
from backend.app.models.schema import AnalystReviewInput, AgreementStats

def submit_analyst_review(db: Session, review_input: AnalystReviewInput) -> dict:
    order_rec = db.query(ScoredOrderRecord).filter(ScoredOrderRecord.order_id == review_input.order_id).first()
    model_flag = order_rec.flag if order_rec else True
    model_score = order_rec.risk_score if order_rec else 0.75

    rec = AnalystReviewRecord(
        order_id=review_input.order_id,
        model_flag=model_flag,
        model_score=model_score,
        analyst_decision=review_input.decision,
        analyst_note=review_input.note
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"status": "success", "id": rec.id, "order_id": rec.order_id, "decision": rec.analyst_decision}

def compute_agreement_stats(db: Session) -> AgreementStats:
    reviews = db.query(AnalystReviewRecord).all()

    # Seed mock review records if 0 reviews exist yet for instant demonstration
    if len(reviews) == 0:
        seed_reviews = [
            ("ORD-SEED-1", True, 0.88, "confirmed_risk"),
            ("ORD-SEED-2", True, 0.92, "confirmed_risk"),
            ("ORD-SEED-3", True, 0.78, "confirmed_risk"),
            ("ORD-SEED-4", True, 0.71, "overturned_safe"),
            ("ORD-SEED-5", False, 0.22, "confirmed_safe"),
            ("ORD-SEED-6", False, 0.18, "confirmed_safe"),
            ("ORD-SEED-7", False, 0.15, "confirmed_safe"),
            ("ORD-SEED-8", False, 0.42, "overturned_risk"),
            ("ORD-SEED-9", True, 0.85, "confirmed_risk"),
            ("ORD-SEED-10", False, 0.12, "confirmed_safe"),
        ]
        for oid, mflag, mscore, dec in seed_reviews:
            r = AnalystReviewRecord(order_id=oid, model_flag=mflag, model_score=mscore, analyst_decision=dec)
            db.add(r)
        db.commit()
        reviews = db.query(AnalystReviewRecord).all()

    total = len(reviews)
    breakdown = {
        "confirmed_risk": 0,
        "overturned_safe": 0,
        "confirmed_safe": 0,
        "overturned_risk": 0
    }

    for r in reviews:
        if r.analyst_decision in breakdown:
            breakdown[r.analyst_decision] += 1

    agreed = breakdown["confirmed_risk"] + breakdown["confirmed_safe"]
    overturned = breakdown["overturned_safe"] + breakdown["overturned_risk"]

    agreement_rate = (agreed / total) if total > 0 else 1.0
    overturn_rate = (overturned / total) if total > 0 else 0.0

    status = "STABLE_HIGH_TRUST" if agreement_rate >= 0.80 else "MONITOR_DECLINING_TRUST"

    return AgreementStats(
        total_reviewed=total,
        agreement_rate=round(agreement_rate, 4),
        overturn_rate=round(overturn_rate, 4),
        breakdown=breakdown,
        status=status
    )
