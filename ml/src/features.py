import os
import json
import pandas as pd
import numpy as np

def run_features():
    raw_dir = "ml/data/raw"
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    print("Loading datasets for feature engineering...")
    labeled = pd.read_csv(os.path.join(processed_dir, "labeled_orders.csv"))
    order_items = pd.read_csv(os.path.join(raw_dir, "olist_order_items_dataset.csv"))
    order_payments = pd.read_csv(os.path.join(raw_dir, "olist_order_payments_dataset.csv"))
    products = pd.read_csv(os.path.join(raw_dir, "olist_products_dataset.csv"))
    sellers = pd.read_csv(os.path.join(raw_dir, "olist_sellers_dataset.csv"))
    cat_translation = pd.read_csv(os.path.join(raw_dir, "product_category_name_translation.csv"))

    # Map category names to english
    products = products.merge(cat_translation, on="product_category_name", how="left")
    products["category_english"] = products["product_category_name_english"].fillna("other")

    # Aggregate order items: order_value, freight_value, primary seller state, primary product category
    items_with_seller = order_items.merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left")
    items_full = items_with_seller.merge(products[["product_id", "category_english"]], on="product_id", how="left")

    item_agg = items_full.groupby("order_id").agg(
        order_value=("price", "sum"),
        freight_value=("freight_value", "sum"),
        seller_state=("seller_state", "first"),
        product_category=("category_english", "first")
    ).reset_index()

    # Aggregate payments: payment_type, installments, total_payment
    # Main payment type (type with highest payment_value)
    payment_main = order_payments.sort_values("payment_value", ascending=False).groupby("order_id").first().reset_index()
    payment_agg = order_payments.groupby("order_id").agg(
        total_payment=("payment_value", "sum"),
        installments=("payment_installments", "max")
    ).reset_index()
    payment_agg["payment_type"] = payment_main["payment_type"]

    # Merge into base labeled dataset
    df = labeled.merge(item_agg, on="order_id", how="left")
    df = df.merge(payment_agg, on="order_id", how="left")

    # Fill NaNs
    df["order_value"] = df["order_value"].fillna(0.0)
    df["freight_value"] = df["freight_value"].fillna(0.0)
    df["total_payment"] = df["total_payment"].fillna(0.0)
    df["installments"] = df["installments"].fillna(1.0)
    df["payment_type"] = df["payment_type"].fillna("credit_card")
    df["product_category"] = df["product_category"].fillna("other")
    df["seller_state"] = df["seller_state"].fillna("UNKNOWN")

    # Derivation rule for discount_flag:
    # Reliable signal: total payment < (order_value + freight_value - threshold)
    total_cost_expected = df["order_value"] + df["freight_value"]
    df["discount_flag"] = ((total_cost_expected - df["total_payment"]) > 1.0).astype(int)

    # Address state mismatch
    df["address_state_mismatch"] = (df["customer_state"] != df["seller_state"]).astype(int)

    # Customer prior order count (expanding count before current order)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df = df.sort_values("order_purchase_timestamp").reset_index(drop=True)

    df["customer_order_count"] = df.groupby("customer_unique_id").cumcount()

    # Top 15 product categories
    top_categories = df["product_category"].value_counts().nlargest(15).index.tolist()
    df["product_category_clean"] = df["product_category"].apply(lambda c: c if c in top_categories else "other")

    # One-hot encoding for payment_type
    payment_types = ["credit_card", "boleto", "voucher", "debit_card"]
    for p_type in payment_types:
        df[f"payment_type_{p_type}"] = (df["payment_type"] == p_type).astype(int)

    # One-hot encoding for top product categories
    for cat in top_categories + ["other"]:
        col_name = f"cat_{cat.replace(' ', '_').replace('&', 'and')}"
        df[col_name] = (df["product_category_clean"] == cat).astype(int)

    # Feature columns specification
    # NOTE: prior_low_review_count is intentionally excluded.
    # It is one of the three conditions that defines return_risk=1 in labeling.py
    # (rule_prior_reviews: prior_low_review_count >= threshold). Including it as a
    # raw feature creates definitional overlap — the model can trivially threshold
    # this single column to recover ~1/3 of the positive class, inflating
    # precision/recall without learning genuine return-risk signal.
    feature_cols = [
        "order_value",
        "freight_value",
        "installments",
        "discount_flag",
        "customer_order_count",
        "address_state_mismatch",
    ] + [f"payment_type_{p}" for p in payment_types] + [
        f"cat_{cat.replace(' ', '_').replace('&', 'and')}" for cat in top_categories + ["other"]
    ]

    # Save feature manifest JSON
    manifest = {
        "features": feature_cols,
        "categorical_encodings": {
            "payment_types": payment_types,
            "top_categories": top_categories
        }
    }
    manifest_path = os.path.join(artifacts_dir, "feature_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved feature manifest ({len(feature_cols)} features) to {manifest_path}")

    # Output processed features table
    output_cols = ["order_id", "customer_unique_id", "order_purchase_timestamp", "return_risk"] + feature_cols
    features_df = df[output_cols]
    output_path = os.path.join(processed_dir, "features.csv")
    features_df.to_csv(output_path, index=False)
    print(f"Saved features table with shape {features_df.shape} to {output_path}")

if __name__ == "__main__":
    run_features()
