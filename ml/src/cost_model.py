import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier

def run_cost_model():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading model and validation dataset for cost modeling...")
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    feature_cols = manifest["features"]
    # Switch to validation features for optimization (preventing test set leakage)
    val_df = pd.read_csv(os.path.join(processed_dir, "val_features.csv"))

    X_val = val_df[feature_cols]
    y_val = val_df["return_risk"].values

    model = XGBClassifier()
    model.load_model(os.path.join(artifacts_dir, "model.json"))

    # Predict probabilities for class 1
    y_prob = model.predict_proba(X_val)[:, 1]

    FP_COST = 500
    FN_COST = 1500
    MAX_REVIEW_RATE = 0.05  # 5% manual review budget operational constraint

    cost_curve = []
    
    # 1. Unconstrained optimization
    best_threshold = 0.5
    min_cost = float("inf")
    best_fp = 0
    best_fn = 0
    best_tp = 0
    best_tn = 0

    # 2. Constrained optimization (Review Rate <= 5%)
    best_threshold_constrained = 0.5
    min_cost_constrained = float("inf")
    constrained_fp = 0
    constrained_fn = 0
    constrained_tp = 0
    constrained_tn = 0
    constrained_found = False

    thresholds = np.arange(0.05, 0.96, 0.01)
    n_samples = len(y_val)

    for t in thresholds:
        t_val = round(float(t), 2)
        y_pred = (y_prob >= t_val).astype(int)

        # FP: actual=0, predicted=1
        fp = int(np.sum((y_val == 0) & (y_pred == 1)))
        # FN: actual=1, predicted=0
        fn = int(np.sum((y_val == 1) & (y_pred == 0)))
        # TP: actual=1, predicted=1
        tp = int(np.sum((y_val == 1) & (y_pred == 1)))
        # TN: actual=0, predicted=0
        tn = int(np.sum((y_val == 0) & (y_pred == 0)))

        total_cost = (fp * FP_COST) + (fn * FN_COST)
        review_rate = (fp + tp) / n_samples

        cost_curve.append({
            "threshold": t_val,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "tn": tn,
            "cost": total_cost,
            "review_rate": review_rate
        })

        # Unconstrained optimization update
        if total_cost < min_cost:
            min_cost = total_cost
            best_threshold = t_val
            best_fp = fp
            best_fn = fn
            best_tp = tp
            best_tn = tn

        # Constrained optimization update (Review Rate <= 5%)
        if review_rate <= MAX_REVIEW_RATE:
            if total_cost < min_cost_constrained:
                min_cost_constrained = total_cost
                best_threshold_constrained = t_val
                constrained_fp = fp
                constrained_fn = fn
                constrained_tp = tp
                constrained_tn = tn
                constrained_found = True

    # If no threshold met the <= 5% constraint, fall back to max threshold (least reviewed)
    if not constrained_found:
        best_threshold_constrained = 0.95
        min_cost_constrained = cost_curve[-1]["cost"]
        constrained_fp = cost_curve[-1]["fp"]
        constrained_fn = cost_curve[-1]["fn"]

    print(f"Optimal Threshold (Unconstrained): {best_threshold:.2f} (Total Cost: ₹{min_cost:,.0f})")
    print(f"Constrained Threshold (Review Rate <= 5%): {best_threshold_constrained:.2f} (Total Cost: ₹{min_cost_constrained:,.0f})")

    config = {
        "threshold": best_threshold,
        "fp_cost": FP_COST,
        "fn_cost": FN_COST,
        "total_cost_at_threshold": min_cost,
        "constrained_threshold": best_threshold_constrained,
        "constrained_total_cost": min_cost_constrained,
        "max_review_rate_constraint": MAX_REVIEW_RATE,
        "cost_curve": cost_curve
    }

    output_path = os.path.join(artifacts_dir, "threshold_config.json")
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Saved threshold config to {output_path}")

if __name__ == "__main__":
    run_cost_model()
