import os
import json
import pandas as pd
import numpy as np
import pickle
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

def run_baselines():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading datasets for baseline models...")
    train_df = pd.read_csv(os.path.join(processed_dir, "train_features.csv"))
    test_df = pd.read_csv(os.path.join(processed_dir, "test_features.csv"))

    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    feature_cols = manifest["features"]
    target_col = "return_risk"

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    # Baseline 1: Dummy (most frequent)
    print("Training Dummy classifier...")
    dummy = DummyClassifier(strategy="prior")
    dummy.fit(X_train, y_train)
    dummy_probs = dummy.predict_proba(X_test)[:, 1]

    # Baseline 2: Logistic Regression (with scaling)
    print("Training Logistic Regression...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    lr = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    lr.fit(X_train_scaled, y_train)
    lr_probs = lr.predict_proba(X_test_scaled)[:, 1]

    # Baseline 3: Random Forest
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_probs = rf.predict_proba(X_test)[:, 1]

    # Save baselines dictionary
    results = {}
    models_dict = {
        "Dummy": dummy_probs,
        "Logistic Regression": lr_probs,
        "Random Forest": rf_probs
    }

    # Evaluate each at default threshold 0.5
    for name, probs in models_dict.items():
        preds = (probs >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        
        results[name] = {
            "precision": float(precision_score(y_test, preds, zero_division=0)),
            "recall": float(recall_score(y_test, preds, zero_division=0)),
            "f1": float(f1_score(y_test, preds, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, probs)),
            "pr_auc": float(average_precision_score(y_test, probs)),
            "confusion_matrix": {
                "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn)
            }
        }
        print(f"{name} metrics -> F1: {results[name]['f1']:.4f}, ROC-AUC: {results[name]['roc_auc']:.4f}")

    # Save baseline metrics
    output_path = os.path.join(artifacts_dir, "baseline_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved baseline results to {output_path}")

if __name__ == "__main__":
    run_baselines()
