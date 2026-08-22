import os
import json
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.db import init_db, SessionLocal, ScoredOrderRecord
from backend.app.core.seed_reviews import seed_analyst_reviews
from backend.app.services.model_loader import model_loader
from backend.app.services.scoring import score_order, build_feature_vector
from backend.app.services.explain import explain_vector
from backend.app.models.schema import OrderInput
from backend.app.api import score, explain, metrics, orders, drift, reviews

def seed_sample_orders():
    db = SessionLocal()
    try:
        count = db.query(ScoredOrderRecord).count()
        if count == 0 and os.path.exists("ml/data/processed/test_features.csv"):
            print("Seeding database with sample test orders for Review Queue...")
            test_df = pd.read_csv("ml/data/processed/test_features.csv")
            # Select top high risk and low risk sample rows
            sample_rows = pd.concat([test_df.head(25), test_df.tail(25)])
            for idx, row in sample_rows.iterrows():
                order_input = OrderInput(
                    order_id=str(row["order_id"]),
                    order_value=float(row["order_value"]),
                    freight_value=float(row["freight_value"]),
                    installments=int(row["installments"]),
                    delivery_delay_days=float(row["delivery_delay_days"]),
                    discount_flag=int(row["discount_flag"]),
                    customer_order_count=int(row["customer_order_count"]),
                    prior_low_review_count=int(row["prior_low_review_count"]),
                    address_state_mismatch=int(row["address_state_mismatch"]),
                    payment_type="boleto" if row.get("payment_type_boleto") == 1 else "credit_card",
                    product_category="health_beauty"
                )
                score_res = score_order(order_input)
                explain_res = explain_vector(score_res["vector_df"], score_res["flag"])

                record = ScoredOrderRecord(
                    order_id=order_input.order_id,
                    order_payload_json=json.dumps(order_input.model_dump()),
                    risk_score=score_res["risk_score"],
                    flag=score_res["flag"],
                    top_factors_json=json.dumps(explain_res["top_factors"]),
                    recommended_action=explain_res["recommended_action"]
                )
                db.add(record)
            db.commit()
            print("Seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    model_loader.load()
    seed_sample_orders()
    seed_analyst_reviews()
    yield
    # Shutdown actions

app = FastAPI(
    title="Return-Risk Scorer API",
    description="Audit-ready explainable return-risk scoring with cost-based threshold optimization",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware explicitly whitelisting Vite dev server on http://localhost:5173
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(score.router)
app.include_router(explain.router)
app.include_router(metrics.router)
app.include_router(orders.router)
app.include_router(drift.router)
app.include_router(reviews.router)

@app.get("/")
def read_root():
    return {"message": "Return-Risk Scorer API is online", "docs": "/docs"}
