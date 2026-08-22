import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ScoredOrderRecord(Base):
    __tablename__ = "scored_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(String, index=True)
    order_payload_json = Column(Text, nullable=False)
    risk_score = Column(Float, nullable=False)
    flag = Column(Boolean, nullable=False)
    top_factors_json = Column(Text, nullable=False)
    recommended_action = Column(String, nullable=False)
    scored_at = Column(DateTime, default=datetime.utcnow)

class ProductionFeaturesRecord(Base):
    __tablename__ = "production_features"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(String, index=True)
    features_json = Column(Text, nullable=False)
    scored_at = Column(DateTime, default=datetime.utcnow)

class AnalystReviewRecord(Base):
    __tablename__ = "analyst_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(String, index=True)
    model_flag = Column(Boolean, nullable=False)
    model_score = Column(Float, nullable=False)
    analyst_decision = Column(String, nullable=False) # "confirmed_risk" | "overturned_safe" | "confirmed_safe" | "overturned_risk"
    analyst_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
