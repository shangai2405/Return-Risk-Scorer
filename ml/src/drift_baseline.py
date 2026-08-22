import os
import json
import pandas as pd
import numpy as np

def run_drift_baseline():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading features dataset and manifest for drift baseline computation...")
    df = pd.read_csv(os.path.join(processed_dir, "features.csv"))
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    feature_cols = manifest["features"]

    # Ensure chronological order by timestamp
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df = df.sort_values("order_purchase_timestamp").reset_index(drop=True)

    # Train split (first 80%)
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size]

    # Sample up to 1000 rows for fast, valid KS-test comparisons
    train_sample_df = train_df[feature_cols].sample(n=min(1000, len(train_df)), random_state=42)

    numeric_features = {}
    categorical_features = {}

    for col in feature_cols:
        vals = train_df[col].dropna().values
        # Check if binary/one-hot or numeric
        unique_vals = np.unique(vals)
        if len(unique_vals) <= 2:
            # Categorical / one-hot feature
            prop = float(np.mean(vals))
            categorical_features[col] = {
                "proportion": prop,
                "count_ones": int(np.sum(vals)),
                "total_count": len(vals)
            }
        else:
            # Numeric continuous feature
            counts, bin_edges = np.histogram(vals, bins=10)
            numeric_features[col] = {
                "bin_edges": [float(x) for x in bin_edges],
                "bin_counts": [int(x) for x in counts],
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "sample": [float(x) for x in train_sample_df[col].values]
            }

    baseline_data = {
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "computed_at": "training_set_snapshot",
        "train_sample_size": len(train_sample_df),
        "total_train_rows": len(train_df)
    }

    output_path = os.path.join(artifacts_dir, "drift_baseline.json")
    with open(output_path, "w") as f:
        json.dump(baseline_data, f, indent=2)
    print(f"Saved drift baseline for {len(feature_cols)} features to {output_path}")

if __name__ == "__main__":
    run_drift_baseline()
