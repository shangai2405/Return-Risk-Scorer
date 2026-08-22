from backend.app.core.db import SessionLocal, AnalystReviewRecord, ScoredOrderRecord, init_db

def seed_analyst_reviews():
    init_db()
    db = SessionLocal()
    try:
        count = db.query(AnalystReviewRecord).count()
        if count == 0:
            print("Seeding 11 realistic analyst review records for demonstration...")
            orders = db.query(ScoredOrderRecord).limit(10).all()
            sample_decisions = [
                ("confirmed_risk", "Confirmed high risk - delayed delivery and low review history"),
                ("confirmed_risk", "Confirmed high risk - Boleto voucher with location mismatch"),
                ("confirmed_risk", "Confirmed high risk - customer repeat complaint history"),
                ("overturned_safe", "Overturned - VIP corporate account verified by support"),
                ("confirmed_safe", "Confirmed safe - standard credit card transaction"),
                ("confirmed_safe", "Confirmed safe - on-time delivery with no prior complaints"),
                ("confirmed_safe", "Confirmed safe - regular repeat customer"),
                ("overturned_risk", "Overturned - flagged by analyst due to suspicious address anomaly"),
                ("confirmed_risk", "Confirmed high risk - severe delivery delay"),
                ("confirmed_safe", "Confirmed safe - verified payment"),
                ("confirmed_risk", "Confirmed high risk - multiple risk signals")
            ]
            for idx, (dec, note) in enumerate(sample_decisions):
                oid = orders[idx].order_id if idx < len(orders) else f"ORD-MANUAL-{idx+1}"
                mflag = orders[idx].flag if idx < len(orders) else (idx % 2 == 0)
                mscore = orders[idx].risk_score if idx < len(orders) else 0.75
                rec = AnalystReviewRecord(
                    order_id=oid,
                    model_flag=mflag,
                    model_score=mscore,
                    analyst_decision=dec,
                    analyst_note=note
                )
                db.add(rec)
            db.commit()
            print("Analyst review records seeded successfully.")
    except Exception as e:
        print(f"Error seeding analyst reviews: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_analyst_reviews()
