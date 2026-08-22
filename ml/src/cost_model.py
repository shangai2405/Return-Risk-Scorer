import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier

def run_cost_model():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading model and test dataset for cost modeling...")
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    feature_cols = manifest["features"]
    test_df = pd.read_csv(os.path.join(processed_dir, "test_features.csv"))

    X_test = test_df[feature_cols]
    y_test = test_df["return_risk"].values

    model = XGBClassifier()
    model.load_model(os.path.join(artifacts_dir, "model.json"))

    # Predict probabilities for class 1
    y_prob = model.predict_proba(X_test)[:, 1]

    FP_COST = 500
    FN_COST = 1500

    cost_curve = []
    best_threshold = 0.5
    min_cost = float("inf")
    best_fp = 0
    best_fn = 0

    thresholds = np.arange(0.05, 0.96, 0.01)
    for t in thresholds:
        t_val = round(float(t), 2)
        y_pred = (y_prob >= t_val).astype(int)

        # FP: actual=0, predicted=1
        fp = int(np.sum((y_test == 0) & (y_pred == 1)))
        # FN: actual=1, predicted=0
        fn = int(np.sum((y_test == 1) & (y_pred == 0)))
        # TP: actual=1, predicted=1
        tp = int(np.sum((y_test == 1) & (y_pred == 1)))
        # TN: actual=0, predicted=0
        tn = int(np.sum((y_test == 0) & (y_pred == 0)))

        total_cost = (fp * FP_COST) + (fn * FN_COST)

        cost_curve.append({
            "threshold": t_val,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "tn": tn,
            "cost": total_cost
        })

        if total_cost < min_cost:
            min_cost = total_cost
            best_threshold = t_val
            best_fp = fp
            best_fn = fn

    print(f"Optimal Threshold: {best_threshold:.2f}")
    print(f"Min Total Cost: ₹{min_cost:,.0f} (FP={best_fp}, FN={best_fn})")

    config = {
        "threshold": best_threshold,
        "fp_cost": FP_COST,
        "fn_cost": FN_COST,
        "total_cost_at_threshold": min_cost,
        "cost_curve": cost_curve
    }

    output_path = os.path.join(artifacts_dir, "threshold_config.json")
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Saved threshold config to {output_path}")

if __name__ == "__main__":
    run_cost_model()
