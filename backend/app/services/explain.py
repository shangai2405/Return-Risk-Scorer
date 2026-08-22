import pandas as pd
import numpy as np
from backend.app.services.model_loader import model_loader

FACTOR_LABELS = {
    "delivery_delay_days": "Fulfillment delivery delay",
    "prior_low_review_count": "Customer history of low review ratings",
    "customer_order_count": "Limited previous order history",
    "address_state_mismatch": "Cross-state seller and customer location",
    "installments": "High number of payment installments",
    "freight_value": "High freight/shipping cost relative to items",
    "order_value": "Order value magnitude",
    "discount_flag": "Deep promotional discount applied",
    "payment_type_boleto": "Payment via Boleto cash slip",
    "payment_type_voucher": "Payment via store voucher",
    "payment_type_credit_card": "Credit card payment structure",
    "payment_type_debit_card": "Debit card payment structure"
}

def format_feature_name(feature_name: str) -> str:
    if feature_name in FACTOR_LABELS:
        return FACTOR_LABELS[feature_name]
    if feature_name.startswith("cat_"):
        cat_clean = feature_name[4:].replace("_", " ").title()
        return f"Product category: {cat_clean}"
    return feature_name.replace("_", " ").title()

def explain_vector(vector_df: pd.DataFrame, flag: bool):
    explainer = model_loader.explainer
    shap_values = explainer(vector_df)
    
    # Extract values for the first (and only) row
    if hasattr(shap_values, "values") and len(shap_values.values.shape) > 1:
        vals = shap_values.values[0]
    else:
        vals = shap_values[0]

    feature_cols = model_loader.feature_cols
    
    factors = []
    for col, val in zip(feature_cols, vals):
        factors.append({
            "feature": col,
            "label": format_feature_name(col),
            "shap_value": float(val)
        })

    # Sort by absolute SHAP value magnitude descending
    factors_sorted = sorted(factors, key=lambda x: abs(x["shap_value"]), reverse=True)
    top_3 = factors_sorted[:3]

    top_factor_descriptions = [f"{item['label']} (SHAP: {item['shap_value']:+.3f})" for item in top_3]
    recommended_action = "Hold for manual review" if flag else "Auto-approve"

    return {
        "top_factors": top_factor_descriptions,
        "factor_details": top_3,
        "recommended_action": recommended_action
    }
