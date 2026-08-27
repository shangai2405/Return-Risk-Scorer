import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier

def run_cost_sensitivity():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading validation features and model for cost-ratio sensitivity analysis...")
    val_df = pd.read_csv(os.path.join(processed_dir, "val_features.csv"))
    
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)
    
    feature_cols = manifest["features"]
    X_val = val_df[feature_cols]
    y_val = val_df["return_risk"].values

    model = XGBClassifier()
    model.load_model(os.path.join(artifacts_dir, "model.json"))

    probs = model.predict_proba(X_val)[:, 1]

    # Generate the threshold-vs-cost analysis table requested in item 7
    fp_cost_fixed = 500
    fn_cost_fixed = 1500
    n_samples = len(y_val)
    
    table_thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
    thresh_cost_table = []

    for t in table_thresholds:
        preds = (probs >= t).astype(int)
        tp = int(np.sum((preds == 1) & (y_val == 1)))
        fp = int(np.sum((preds == 1) & (y_val == 0)))
        fn = int(np.sum((preds == 0) & (y_val == 1)))
        tn = int(np.sum((preds == 0) & (y_val == 0)))
        
        # Calculations
        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        review_rate = float((tp + fp) / n_samples)
        expected_cost = int(fp * fp_cost_fixed + fn * fn_cost_fixed)

        thresh_cost_table.append({
            "threshold": t,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "review_rate": round(review_rate, 4),
            "fp": fp,
            "fn": fn,
            "expected_financial_loss": expected_cost
        })

    # Save threshold-vs-cost analysis table
    table_output_path = os.path.join(artifacts_dir, "threshold_vs_cost_table.json")
    with open(table_output_path, "w") as f:
        json.dump(thresh_cost_table, f, indent=2)
    print(f"Saved threshold-vs-cost table analysis to {table_output_path}")

    # Cost ratios sweep
    fn_cost_sweep = [500, 750, 1000, 1250, 1500, 2000, 2500, 3000, 4000, 5000]
    sweep_results = []
    thresholds = np.arange(0.05, 0.96, 0.01)

    t_1_3 = None
    t_1_1_5 = None
    t_1_4_5 = None

    for fn_c in fn_cost_sweep:
        best_t = 0.5
        min_cost = float("inf")

        for t in thresholds:
            preds = (probs >= t).astype(int)
            fp = np.sum((preds == 1) & (y_val == 0))
            fn = np.sum((preds == 0) & (y_val == 1))
            total_c = fp * fp_cost_fixed + fn * fn_c

            if total_c < min_cost:
                min_cost = total_c
                best_t = float(t)

        ratio_str = f"1:{fn_c / fp_cost_fixed:.1f}".replace(".0", "")
        sweep_results.append({
            "fn_cost": fn_c,
            "ratio": ratio_str,
            "optimal_threshold": round(best_t, 2),
            "total_cost": int(min_cost)
        })

        if fn_c == 1500:
            t_1_3 = best_t
        if fn_c == 750:
            t_1_1_5 = best_t
        if fn_c == 2000:
            t_1_4_5 = best_t

    # Compute stability note around 1:3 ratio
    swing = abs((t_1_4_5 or t_1_3) - (t_1_1_5 or t_1_3)) if (t_1_1_5 and t_1_4_5) else 0.05
    if swing <= 0.15:
        stability_note = f"Threshold choice is stable (swing of {swing:.2f} <= 0.15) across realistic cost assumptions in the 1:1.5 to 1:4 ratio range where our ₹500/₹1,500 estimate sits."
    else:
        stability_note = f"Threshold is sensitive to FN cost estimate (swing of {swing:.2f} > 0.15) across 1:1.5 to 1:4 ratio range — see documentation for business cost rationale."

    output_data = {
        "fp_cost_fixed": fp_cost_fixed,
        "sweep": sweep_results,
        "chosen_ratio": "1:3",
        "chosen_fn_cost": 1500,
        "stability_note": stability_note
    }

    output_path = os.path.join(artifacts_dir, "cost_sensitivity.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved cost sensitivity analysis ({len(sweep_results)} ratio sweeps) to {output_path}")
    print(f"Stability Note: {stability_note}")

if __name__ == "__main__":
    run_cost_sensitivity()
