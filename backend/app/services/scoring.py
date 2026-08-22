import numpy as np
import pandas as pd
from backend.app.models.schema import OrderInput
from backend.app.services.model_loader import model_loader

def build_feature_vector(order_input: OrderInput) -> pd.DataFrame:
    manifest = model_loader.feature_manifest
    feature_cols = model_loader.feature_cols

    # Initialize dict with zero for all manifest features
    data = {col: 0.0 for col in feature_cols}

    # Set numeric fields
    data["order_value"] = float(order_input.order_value)
    data["freight_value"] = float(order_input.freight_value)
    data["installments"] = float(order_input.installments)
    data["delivery_delay_days"] = float(order_input.delivery_delay_days)
    data["discount_flag"] = int(order_input.discount_flag)
    data["customer_order_count"] = int(order_input.customer_order_count)
    data["prior_low_review_count"] = int(order_input.prior_low_review_count)
    data["address_state_mismatch"] = int(order_input.address_state_mismatch)

    # Set payment_type one-hot
    p_col = f"payment_type_{order_input.payment_type}"
    if p_col in data:
        data[p_col] = 1.0

    # Set category one-hot
    cat = order_input.product_category
    top_categories = manifest["categorical_encodings"]["top_categories"]
    if cat not in top_categories:
        cat = "other"
    cat_col = f"cat_{cat.replace(' ', '_').replace('&', 'and')}"
    if cat_col in data:
        data[cat_col] = 1.0

    # Create DataFrame with exact column order
    vector_df = pd.DataFrame([data])[feature_cols]
    return vector_df

def score_order(order_input: OrderInput):
    vector_df = build_feature_vector(order_input)
    prob = float(model_loader.model.predict_proba(vector_df)[0, 1])
    threshold = model_loader.threshold
    flag = prob >= threshold

    return {
        "risk_score": prob,
        "flag": flag,
        "threshold": threshold,
        "vector_df": vector_df
    }
