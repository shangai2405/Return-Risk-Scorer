import os
import json
import pandas as pd
import numpy as np

"""
PREDICTION POINT & TARGET METHODOLOGY DEFINITION:

1. Prediction Point:
   - Evaluated immediately after order placement, before fulfillment.
   - Only information available at this time is allowed in the feature pipeline.
   - Outcomes known after placement (such as actual delivery delays or review scores) are STRICTLY EXCLUDED.

2. Target Definition (Empirical Proxy):
   - 1 = observed/proxy risky outcome (low review, extreme delivery delay, or high prior customer review complaints)
   - 0 = otherwise
   - Note on Dataset Limitation: The Olist dataset does not contain clean, direct RTO (Return to Origin) 
     labels. We therefore construct an empirical proxy target using observed order outcomes.
   - Critical Ordering: This target is generated BEFORE the predictive feature pipeline is executed, 
     allowing us to use outcome variables for the label while filtering them out of model features.
"""

def run_labeling():

    raw_dir = "ml/data/raw"
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    print("Loading raw datasets...")
    orders = pd.read_csv(os.path.join(raw_dir, "olist_orders_dataset.csv"))
    reviews = pd.read_csv(os.path.join(raw_dir, "olist_order_reviews_dataset.csv"))
    customers = pd.read_csv(os.path.join(raw_dir, "olist_customers_dataset.csv"))

    # Parse timestamps
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    orders["order_delivered_customer_date"] = pd.to_datetime(orders["order_delivered_customer_date"])
    orders["order_estimated_delivery_date"] = pd.to_datetime(orders["order_estimated_delivery_date"])

    # Merge orders with customers to get customer_unique_id
    df = orders.merge(customers, on="customer_id", how="inner")

    # Aggregate reviews per order (take min review score if multiple reviews)
    review_agg = reviews.groupby("order_id")["review_score"].min().reset_index()
    df = df.merge(review_agg, on="order_id", how="left")

    # Compute delivery_delay_days: actual delivery date minus estimated delivery date
    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400.0

    df["delivery_delay_days"] = df["delivery_delay_days"].fillna(0.0)

    # Sort chronologically by purchase timestamp to calculate prior history accurately without leakage
    df = df.sort_values("order_purchase_timestamp").reset_index(drop=True)

    # Flag individual low review
    df["is_low_review"] = (df["review_score"] <= 2).astype(int)

    # Compute expanding prior low review count per customer_unique_id strictly before current order
    df["prior_low_review_count"] = (
        df.groupby("customer_unique_id")["is_low_review"]
        .transform(lambda s: s.shift(1).fillna(0).cumsum())
    )

    # Compute expanding customer prior order count
    df["prior_order_count"] = df.groupby("customer_unique_id").cumcount()

    print("\n--- EMPIRICAL DISTRIBUTION ANALYSIS ---")
    
    # 1. Delivery delay distribution
    delays = df["delivery_delay_days"]
    p75 = float(np.percentile(delays, 75))
    p90 = float(np.percentile(delays, 90))
    p95 = float(np.percentile(delays, 95))
    
    print(f"Delivery Delay Percentiles: 75th={p75:.2f} days, 90th={p90:.2f} days, 95th={p95:.2f} days")
    
    # Set delay threshold to 90th percentile rounded to nearest whole day
    delay_thresh_days = int(round(p90))
    # Ensure minimum delay threshold of 1 if rounded percentile is <= 0
    if delay_thresh_days <= 0:
        delay_thresh_days = max(1, int(round(p95)))
    
    print(f"Computed Delay Threshold (90th percentile rounded): {delay_thresh_days} days")

    # 2. Prior low-review count distribution across repeat customers (customers with >= 1 prior order)
    repeat_customers = df[df["prior_order_count"] >= 1]
    prior_counts = repeat_customers["prior_low_review_count"].value_counts().sort_index()
    print("\nPrior Low-Review Count Distribution (Repeat Customers):")
    print(prior_counts)

    # Smallest value where fewer than ~10% of repeat customers exceed it
    n_repeat = len(repeat_customers) if len(repeat_customers) > 0 else len(df)
    prior_low_thresh = 1
    for val in sorted(prior_counts.index):
        pct_exceeding = (repeat_customers["prior_low_review_count"] > val).sum() / n_repeat
        if pct_exceeding < 0.10:
            prior_low_thresh = int(val + 1)
            break

    print(f"Computed Prior Low-Review Threshold: >={prior_low_thresh}")

    # Output ml/artifacts/labeling_thresholds.json
    thresholds_config = {
        "delay_threshold_days": delay_thresh_days,
        "delay_percentile_used": 90,
        "prior_low_review_threshold": prior_low_thresh,
        "prior_low_review_rationale": "smallest value where <10% of repeat customers exceed it",
        "review_score_threshold": 2,
        "review_score_rationale": "Olist's own rating scale treats 1-2 as explicit dissatisfaction"
    }

    thresh_path = os.path.join(artifacts_dir, "labeling_thresholds.json")
    with open(thresh_path, "w") as f:
        json.dump(thresholds_config, f, indent=2)
    print(f"\nSaved empirical labeling thresholds to {thresh_path}")

    # READ BACK FROM JSON AS SINGLE SOURCE OF TRUTH
    with open(thresh_path, "r") as f:
        loaded_thresh = json.load(f)

    d_thresh = loaded_thresh["delay_threshold_days"]
    p_thresh = loaded_thresh["prior_low_review_threshold"]
    r_thresh = loaded_thresh["review_score_threshold"]

    # Apply labeling rule from loaded JSON thresholds
    rule_low_review = df["review_score"] <= r_thresh
    rule_delay = df["delivery_delay_days"] > d_thresh
    rule_prior_reviews = df["prior_low_review_count"] >= p_thresh

    df["return_risk"] = (rule_low_review | rule_delay | rule_prior_reviews).astype(int)

    # Log class balance
    total_orders = len(df)
    pos_count = int(df["return_risk"].sum())
    neg_count = total_orders - pos_count
    pos_percent = (pos_count / total_orders) * 100

    print("\n--- FINAL LABELED DATASET SUMMARY ---")
    print(f"Total labeled orders: {total_orders}")
    print(f"Positive (High Return Risk): {pos_count} ({pos_percent:.2f}%)")
    print(f"Negative (Low Return Risk): {neg_count} ({100 - pos_percent:.2f}%)")

    output_path = os.path.join(processed_dir, "labeled_orders.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved labeled dataset to {output_path}")

if __name__ == "__main__":
    run_labeling()
