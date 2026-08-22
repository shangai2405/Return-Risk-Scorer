import os
import json
import pickle
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import shap

def run_train():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading features dataset and manifest...")
    df = pd.read_csv(os.path.join(processed_dir, "features.csv"))
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    feature_cols = manifest["features"]
    target_col = "return_risk"

    # Ensure chronological order by timestamp
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df = df.sort_values("order_purchase_timestamp").reset_index(drop=True)

    # 80/20 chronological split
    n = len(df)
    train_size = int(n * 0.8)

    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    # Compute scale_pos_weight
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0

    print(f"Train samples: {len(X_train)} (Positive: {pos_count}, Negative: {neg_count})")
    print(f"Test samples: {len(X_test)}")
    print(f"scale_pos_weight: {scale_pos_weight:.3f}")

    # Train XGBClassifier
    print("Training XGBClassifier model...")
    model = XGBClassifier(
        max_depth=5,
        n_estimators=300,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=42
    )
    model.fit(X_train, y_train)

    # Save model.json
    model_path = os.path.join(artifacts_dir, "model.json")
    model.save_model(model_path)
    print(f"Saved model to {model_path}")

    # Fit SHAP TreeExplainer and save explainer.pkl
    print("Fitting SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    explainer_path = os.path.join(artifacts_dir, "explainer.pkl")
    with open(explainer_path, "wb") as f:
        pickle.dump(explainer, f)
    print(f"Saved SHAP explainer to {explainer_path}")

    # Save test set partition for cost modeling & evaluation scripts
    test_df.to_csv(os.path.join(processed_dir, "test_features.csv"), index=False)
    print(f"Saved test features partition ({len(test_df)} rows) to test_features.csv")

if __name__ == "__main__":
    run_train()
