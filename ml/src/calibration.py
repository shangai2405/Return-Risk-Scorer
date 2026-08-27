import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import brier_score_loss

def run_calibration():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading model and validation dataset for probability calibration check...")
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    feature_cols = manifest["features"]
    val_df = pd.read_csv(os.path.join(processed_dir, "val_features.csv"))

    X_val = val_df[feature_cols]
    y_val = val_df["return_risk"].values

    model = XGBClassifier()
    model.load_model(os.path.join(artifacts_dir, "model.json"))

    probs = model.predict_proba(X_val)[:, 1]
    brier_val = float(brier_score_loss(y_val, probs))

    # Divide probability range into 5 bins
    bins = np.linspace(0, 1, 6)
    bin_centers = []
    observed_rates = []
    counts = []

    for i in range(len(bins)-1):
        lower = bins[i]
        upper = bins[i+1]
        mask = (probs >= lower) & (probs < upper)
        
        count = int(np.sum(mask))
        if count > 0:
            observed_rate = float(np.mean(y_val[mask]))
        else:
            observed_rate = 0.0
            
        bin_centers.append(float((lower + upper) / 2))
        observed_rates.append(observed_rate)
        counts.append(count)

    calibration_data = {
        "brier_score": brier_val,
        "bins": {
            "bin_centers": bin_centers,
            "observed_positive_rates": observed_rates,
            "sample_counts": counts
        }
    }

    output_path = os.path.join(artifacts_dir, "calibration.json")
    with open(output_path, "w") as f:
        json.dump(calibration_data, f, indent=2)

    print(f"Calibration completed. Brier Score: {brier_val:.4f}")
    print(f"Calibration data saved to {output_path}")

if __name__ == "__main__":
    run_calibration()
