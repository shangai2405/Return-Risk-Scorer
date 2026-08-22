import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

def run_evaluate():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading test data and threshold config...")
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    with open(os.path.join(artifacts_dir, "threshold_config.json"), "r") as f:
        thresh_config = json.load(f)

    cost_opt_thresh = thresh_config["threshold"]
    feature_cols = manifest["features"]

    test_df = pd.read_csv(os.path.join(processed_dir, "test_features.csv"))
    X_test = test_df[feature_cols]
    y_test = test_df["return_risk"].values

    model = XGBClassifier()
    model.load_model(os.path.join(artifacts_dir, "model.json"))

    y_prob = model.predict_proba(X_test)[:, 1]
    roc_auc = float(roc_auc_score(y_test, y_prob))

    FP_COST = thresh_config["fp_cost"]
    FN_COST = thresh_config["fn_cost"]

    # Compute metrics at cost-optimal threshold
    y_pred_cost = (y_prob >= cost_opt_thresh).astype(int)
    tn_c, fp_c, fn_c, tp_c = confusion_matrix(y_test, y_pred_cost).ravel()

    prec_c = float(precision_score(y_test, y_pred_cost, zero_division=0))
    rec_c = float(recall_score(y_test, y_pred_cost, zero_division=0))
    f1_c = float(f1_score(y_test, y_pred_cost, zero_division=0))
    cost_c = int(fp_c * FP_COST + fn_c * FN_COST)

    # Find F1-optimal threshold
    best_f1 = -1.0
    f1_opt_thresh = 0.5
    for t in np.arange(0.05, 0.96, 0.01):
        t_val = round(float(t), 2)
        y_pred = (y_prob >= t_val).astype(int)
        score = f1_score(y_test, y_pred, zero_division=0)
        if score > best_f1:
            best_f1 = score
            f1_opt_thresh = t_val

    y_pred_f1 = (y_prob >= f1_opt_thresh).astype(int)
    tn_f, fp_f, fn_f, tp_f = confusion_matrix(y_test, y_pred_f1).ravel()
    prec_f = float(precision_score(y_test, y_pred_f1, zero_division=0))
    rec_f = float(recall_score(y_test, y_pred_f1, zero_division=0))
    f1_f = float(f1_score(y_test, y_pred_f1, zero_division=0))
    cost_f = int(fp_f * FP_COST + fn_f * FN_COST)

    # Naive Baseline Policies
    total_pos = int(np.sum(y_test == 1))
    total_neg = int(np.sum(y_test == 0))

    cost_flag_nothing = total_pos * FN_COST
    cost_flag_everything = total_neg * FP_COST

    savings_vs_flag_nothing = cost_flag_nothing - cost_c
    savings_vs_flag_everything = cost_flag_everything - cost_c

    eval_results = {
        "cost_optimal": {
            "threshold": cost_opt_thresh,
            "precision": prec_c,
            "recall": rec_c,
            "f1": f1_c,
            "roc_auc": roc_auc,
            "confusion_matrix": {"tp": int(tp_c), "tn": int(tn_c), "fp": int(fp_c), "fn": int(fn_c)},
            "total_cost": cost_c
        },
        "f1_optimal": {
            "threshold": f1_opt_thresh,
            "precision": prec_f,
            "recall": rec_f,
            "f1": f1_f,
            "roc_auc": roc_auc,
            "confusion_matrix": {"tp": int(tp_f), "tn": int(tn_f), "fp": int(fp_f), "fn": int(fn_f)},
            "total_cost": cost_f
        },
        "naive_baselines": {
            "flag_nothing": {
                "threshold": 1.0,
                "total_cost": cost_flag_nothing,
                "fn_count": total_pos,
                "fp_count": 0
            },
            "flag_everything": {
                "threshold": 0.0,
                "total_cost": cost_flag_everything,
                "fn_count": 0,
                "fp_count": total_neg
            }
        },
        "cost_savings_vs_f1_optimal": cost_f - cost_c,
        "cost_savings_vs_flag_nothing": savings_vs_flag_nothing,
        "cost_savings_vs_flag_everything": savings_vs_flag_everything
    }

    print("\n--- EVALUATION SUMMARY ---")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"Cost-Optimal Threshold ({cost_opt_thresh}): Precision={prec_c:.4f}, Recall={rec_c:.4f}, F1={f1_c:.4f}, Total Cost=₹{cost_c:,.0f}")
    print(f"F1-Optimal Threshold ({f1_opt_thresh}): Precision={prec_f:.4f}, Recall={rec_f:.4f}, F1={f1_f:.4f}, Total Cost=₹{cost_f:,.0f}")
    print(f"Flag Nothing Policy Cost: ₹{cost_flag_nothing:,.0f}")
    print(f"Flag Everything Policy Cost: ₹{cost_flag_everything:,.0f}")
    print(f"--> Savings vs Flag Nothing: ₹{savings_vs_flag_nothing:,.0f}")
    print(f"--> Savings vs Flag Everything: ₹{savings_vs_flag_everything:,.0f}")

    output_path = os.path.join(artifacts_dir, "eval_results.json")
    with open(output_path, "w") as f:
        json.dump(eval_results, f, indent=2)
    print(f"Saved evaluation results to {output_path}")

if __name__ == "__main__":
    run_evaluate()
