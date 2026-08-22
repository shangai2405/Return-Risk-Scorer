from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class OrderInput(BaseModel):
    order_id: Optional[str] = "ORD-TEST-1001"
    order_value: float = Field(..., example=250.0)
    freight_value: float = Field(..., example=25.0)
    installments: int = Field(1, example=3)
    delivery_delay_days: float = Field(0.0, example=8.5)
    discount_flag: int = Field(0, example=0)
    customer_order_count: int = Field(0, example=1)
    prior_low_review_count: int = Field(0, example=2)
    address_state_mismatch: int = Field(0, example=1)
    payment_type: str = Field("credit_card", example="boleto")
    product_category: str = Field("other", example="health_beauty")

class FactorBreakdown(BaseModel):
    feature: str
    label: str
    shap_value: float

class ScoreResponse(BaseModel):
    order_id: str
    risk_score: float
    flag: bool
    threshold: float
    top_factors: List[str]
    factor_details: List[FactorBreakdown]
    recommended_action: str

class OrderRecordResponse(BaseModel):
    id: int
    order_id: str
    order_payload: Dict[str, Any]
    risk_score: float
    flag: bool
    top_factors: List[str]
    recommended_action: str
    scored_at: str

class MetricsResponse(BaseModel):
    precision: float
    recall: float
    f1: float
    roc_auc: float
    chosen_threshold: float
    fp_cost: int
    fn_cost: int
    total_cost_at_threshold: int
    cost_curve: List[Dict[str, Any]]
    eval_results: Dict[str, Any]
    cost_sensitivity: Optional[Dict[str, Any]] = None

class AnalystReviewInput(BaseModel):
    order_id: str
    decision: str = Field(..., example="confirmed_risk") # "confirmed_risk" | "overturned_safe" | "confirmed_safe" | "overturned_risk"
    note: Optional[str] = None

class AgreementStats(BaseModel):
    total_reviewed: int
    agreement_rate: float
    overturn_rate: float
    breakdown: Dict[str, int]
    status: str
