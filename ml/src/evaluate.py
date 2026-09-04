import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss

def run_evaluate():
    processed_dir = "ml/data/processed"
    artifacts_dir = "ml/artifacts"

    print("Loading test data, thresholds, and calibration configurations...")
    with open(os.path.join(artifacts_dir, "feature_manifest.json"), "r") as f:
        manifest = json.load(f)

    with open(os.path.join(artifacts_dir, "threshold_config.json"), "r") as f:
        thresh_config = json.load(f)

    # Load baseline results if they exist
    baseline_path = os.path.join(artifacts_dir, "baseline_results.json")
    baselines = {}
    if os.path.exists(baseline_path):
        with open(baseline_path, "r") as f:
            baselines = json.load(f)

    # Load calibration stats
    calib_path = os.path.join(artifacts_dir, "calibration.json")
    brier_val = 0.0
    if os.path.exists(calib_path):
        with open(calib_path, "r") as f:
            calib_data = json.load(f)
            brier_val = calib_data.get("brier_score", 0.0)

    cost_opt_thresh = thresh_config["threshold"]
    constrained_thresh = thresh_config.get("constrained_threshold", 0.5)
    feature_cols = manifest["features"]

    # Load Strictly UNTOUCHED Test Dataset
    test_df = pd.read_csv(os.path.join(processed_dir, "test_features.csv"))
    X_test = test_df[feature_cols]
    y_test = test_df["return_risk"].values

    model = XGBClassifier()
    model.load_model(os.path.join(artifacts_dir, "model.json"))

    y_prob = model.predict_proba(X_test)[:, 1]
    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    brier_test = float(brier_score_loss(y_test, y_prob))

    FP_COST = thresh_config["fp_cost"]
    FN_COST = thresh_config["fn_cost"]
    n_test = len(y_test)

    # 1. Evaluate Cost-Optimal Threshold (optimized on validation set)
    y_pred_cost = (y_prob >= cost_opt_thresh).astype(int)
    tn_c, fp_c, fn_c, tp_c = confusion_matrix(y_test, y_pred_cost).ravel()

    prec_c = float(precision_score(y_test, y_pred_cost, zero_division=0))
    rec_c = float(recall_score(y_test, y_pred_cost, zero_division=0))
    f1_c = float(f1_score(y_test, y_pred_cost, zero_division=0))
    cost_c = int(fp_c * FP_COST + fn_c * FN_COST)
    rev_rate_c = float((fp_c + tp_c) / n_test)

    # 2. Evaluate Constrained Threshold (optimized on validation set, review rate <= 5%)
    y_pred_const = (y_prob >= constrained_thresh).astype(int)
    tn_co, fp_co, fn_co, tp_co = confusion_matrix(y_test, y_pred_const).ravel()

    prec_co = float(precision_score(y_test, y_pred_const, zero_division=0))
    rec_co = float(recall_score(y_test, y_pred_const, zero_division=0))
    f1_co = float(f1_score(y_test, y_pred_const, zero_division=0))
    cost_co = int(fp_co * FP_COST + fn_co * FN_COST)
    rev_rate_co = float((fp_co + tp_co) / n_test)

    # 3. Find F1-optimal threshold — swept on the VALIDATION set to avoid test-set leakage.
    # The previously used test-set sweep was an inconsistency: the cost-optimal and constrained
    # thresholds are both selected on val, so this comparison baseline must be too.
    val_df = pd.read_csv(os.path.join(processed_dir, "val_features.csv"))
    X_val = val_df[feature_cols]
    y_val = val_df["return_risk"].values
    y_prob_val = model.predict_proba(X_val)[:, 1]

    best_f1_val = -1.0
    f1_opt_thresh = 0.5
    for t in np.arange(0.05, 0.96, 0.01):
        t_val = round(float(t), 2)
        y_pred_v = (y_prob_val >= t_val).astype(int)
        score = f1_score(y_val, y_pred_v, zero_division=0)
        if score > best_f1_val:
            best_f1_val = score
            f1_opt_thresh = t_val

    # Apply the val-selected F1 threshold to the test set for final evaluation
    y_pred_f1 = (y_prob >= f1_opt_thresh).astype(int)
    tn_f, fp_f, fn_f, tp_f = confusion_matrix(y_test, y_pred_f1).ravel()
    prec_f = float(precision_score(y_test, y_pred_f1, zero_division=0))
    rec_f = float(recall_score(y_test, y_pred_f1, zero_division=0))
    f1_f = float(f1_score(y_test, y_pred_f1, zero_division=0))
    cost_f = int(fp_f * FP_COST + fn_f * FN_COST)
    rev_rate_f = float((fp_f + tp_f) / n_test)

    # Naive Baseline Policies
    total_pos = int(np.sum(y_test == 1))
    total_neg = int(np.sum(y_test == 0))

    cost_flag_nothing = total_pos * FN_COST
    cost_flag_everything = total_neg * FP_COST

    savings_vs_flag_nothing = cost_flag_nothing - cost_c
    savings_vs_flag_everything = cost_flag_everything - cost_c

    # 4. Segment-Level Evaluation
    segments_results = {}
    
    # Segment definitions
    # COD vs Prepaid
    test_df["is_cod"] = test_df["payment_type_boleto"] == 1
    # Customer type
    test_df["is_new_customer"] = test_df["customer_order_count"] <= 0
    # Order Value (Low < P33, High > P66)
    v_p33 = np.percentile(test_df["order_value"], 33)
    v_p66 = np.percentile(test_df["order_value"], 66)
    
    def get_val_tier(v):
        if v < v_p33: return "low"
        if v > v_p66: return "high"
        return "mid"
    test_df["val_tier"] = test_df["order_value"].apply(get_val_tier)

    segment_definitions = {
        "COD": test_df["is_cod"] == True,
        "Prepaid": test_df["is_cod"] == False,
        "New Customer": test_df["is_new_customer"] == True,
        "Repeat Customer": test_df["is_new_customer"] == False,
        "Low Value Order": test_df["val_tier"] == "low",
        "Mid Value Order": test_df["val_tier"] == "mid",
        "High Value Order": test_df["val_tier"] == "high"
    }

    for seg_name, mask in segment_definitions.items():
        sub_y = y_test[mask]
        sub_prob = y_prob[mask]
        
        if len(sub_y) > 0:
            sub_pred = (sub_prob >= cost_opt_thresh).astype(int)
            tn_s, fp_s, fn_s, tp_s = confusion_matrix(sub_y, sub_pred, labels=[0, 1]).ravel()
            
            prec_s = float(precision_score(sub_y, sub_pred, zero_division=0))
            rec_s = float(recall_score(sub_y, sub_pred, zero_division=0))
            cost_s = int(fp_s * FP_COST + fn_s * FN_COST)
            rev_s = float((fp_s + tp_s) / len(sub_y))
            
            segments_results[seg_name] = {
                "count": len(sub_y),
                "precision": round(prec_s, 4),
                "recall": round(rec_s, 4),
                "review_rate": round(rev_s, 4),
                "cost": cost_s
            }

    eval_results = {
        "cost_optimal": {
            "threshold": cost_opt_thresh,
            "precision": prec_c,
            "recall": rec_c,
            "f1": f1_c,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "brier_score": brier_test,
            "review_rate": rev_rate_c,
            # Business meaning of confusion matrix:
            # FP -> Legitimate order incorrectly reviewed (creates friction, support cost)
            # FN -> Risky order allowed through (leads to RTO / refund losses)
            "confusion_matrix": {"tp": int(tp_c), "tn": int(tn_c), "fp": int(fp_c), "fn": int(fn_c)},
            "total_cost": cost_c
        },
        "constrained_operational": {
            "threshold": constrained_thresh,
            "precision": prec_co,
            "recall": rec_co,
            "f1": f1_co,
            "review_rate": rev_rate_co,
            "confusion_matrix": {"tp": int(tp_co), "tn": int(tn_co), "fp": int(fp_co), "fn": int(fn_co)},
            "total_cost": cost_co
        },
        "f1_optimal": {
            "threshold": f1_opt_thresh,
            "precision": prec_f,
            "recall": rec_f,
            "f1": f1_f,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "review_rate": rev_rate_f,
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
        "baselines_comparisons": baselines,
        "segment_evaluation": segments_results,
        "cost_savings_vs_f1_optimal": cost_f - cost_c,
        "cost_savings_vs_flag_nothing": savings_vs_flag_nothing,
        "cost_savings_vs_flag_everything": savings_vs_flag_everything
    }

    print("\n--- EVALUATION SUMMARY ---")
    print(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | Brier Score: {brier_test:.4f}")
    print(f"Cost-Optimal Threshold ({cost_opt_thresh}): Precision={prec_c:.4f}, Recall={rec_c:.4f}, F1={f1_c:.4f}, Review Rate={rev_rate_c*100:.2f}%, Total Cost=₹{cost_c:,.0f}")
    print(f"Constrained (<=5% Review) Threshold ({constrained_thresh}): Precision={prec_co:.4f}, Recall={rec_co:.4f}, F1={f1_co:.4f}, Review Rate={rev_rate_co*100:.2f}%, Total Cost=₹{cost_co:,.0f}")
    print(f"F1-Optimal Threshold ({f1_opt_thresh}): Precision={prec_f:.4f}, Recall={rec_f:.4f}, F1={f1_f:.4f}, Review Rate={rev_rate_f*100:.2f}%, Total Cost=₹{cost_f:,.0f}")
    print(f"Flag Nothing Policy Cost: ₹{cost_flag_nothing:,.0f}")
    print(f"Flag Everything Policy Cost: ₹{cost_flag_everything:,.0f}")
    print(f"--> Savings vs Flag Nothing: ₹{savings_vs_flag_nothing:,.0f}")
    
    print("\nSegment Evaluation:")
    for seg, metrics in segments_results.items():
        print(f" - {seg:15} (N={metrics['count']}): Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}, Review Rate={metrics['review_rate']*100:.2f}%, Cost=₹{metrics['cost']:,.0f}")

    output_path = os.path.join(artifacts_dir, "eval_results.json")
    with open(output_path, "w") as f:
        json.dump(eval_results, f, indent=2)
    print(f"\nSaved evaluation results to {output_path}")

if __name__ == "__main__":
    run_evaluate()
