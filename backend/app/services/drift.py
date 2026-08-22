import os
import json
import math
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.db import ProductionFeaturesRecord

# Plain-language explanation templates for features
DRIFT_EXPLANATIONS = {
    "delivery_delay_days": "Fulfillment delivery delays are shifting from training baseline — risk model may misestimate return probability.",
    "order_value": "Customer basket size (order value) is trending higher/lower than historical training baseline.",
    "freight_value": "Logistics & freight shipping charges differ significantly from training baseline distribution.",
    "prior_low_review_count": "Customer repeat dissatisfaction history profile shows statistical distribution shift.",
    "customer_order_count": "Customer repeat order frequency pattern deviates from baseline training population.",
    "installments": "Payment installment plans selected by buyers show significant distribution shift.",
    "payment_type_boleto": "Boleto cash voucher payment usage proportion shifted from training baseline.",
    "payment_type_credit_card": "Credit card payment usage proportion shifted from training baseline.",
    "address_state_mismatch": "Cross-state buyer/seller geographic mismatch proportion changed significantly."
}

class DriftService:
    def __init__(self):
        self.baseline = None
        self.load_baseline()

    def load_baseline(self):
        baseline_path = os.path.join(settings.ARTIFACTS_DIR, "drift_baseline.json")
        if os.path.exists(baseline_path):
            with open(baseline_path, "r") as f:
                self.baseline = json.load(f)
            print("Drift baseline successfully loaded into memory!")
        else:
            print("Warning: drift_baseline.json not found!")

    def calculate_psi(self, expected_prop: float, actual_prop: float) -> float:
        # Clip proportions to avoid log(0)
        e1 = max(0.001, min(0.999, expected_prop))
        e0 = 1.0 - e1
        a1 = max(0.001, min(0.999, actual_prop))
        a0 = 1.0 - a1

        psi_1 = (a1 - e1) * math.log(a1 / e1)
        psi_0 = (a0 - e0) * math.log(a0 / e0)
        return float(psi_1 + psi_0)

    def compute_drift(self, db: Session, window_size: int = 200) -> dict:
        if not self.baseline:
            self.load_baseline()

        # Query recent production feature records
        records = db.query(ProductionFeaturesRecord).order_by(ProductionFeaturesRecord.id.desc()).limit(window_size).all()
        
        if len(records) > 0:
            prod_rows = [json.loads(r.features_json) for r in records]
            prod_df = pd.DataFrame(prod_rows)
        else:
            # If no live production records yet, load sample test rows for demonstration
            test_path = os.path.abspath("ml/data/processed/test_features.csv")
            if os.path.exists(test_path):
                test_df = pd.read_csv(test_path)
                manifest_path = os.path.join(settings.ARTIFACTS_DIR, "feature_manifest.json")
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                prod_df = test_df[manifest["features"]].head(window_size)
            else:
                prod_df = pd.DataFrame()

        results = []
        drift_count = 0

        numeric_baseline = self.baseline.get("numeric_features", {}) if self.baseline else {}
        categorical_baseline = self.baseline.get("categorical_features", {}) if self.baseline else {}

        # 1. Evaluate Numeric Features (KS Test)
        for col, meta in numeric_baseline.items():
            if col in prod_df.columns and len(prod_df) >= 5:
                ref_sample = meta.get("sample", [])
                prod_sample = prod_df[col].dropna().values

                if len(ref_sample) > 0 and len(prod_sample) > 0:
                    stat_res = ks_2samp(ref_sample, prod_sample)
                    p_val = float(stat_res.pvalue)
                    ks_stat = float(stat_res.statistic)
                    is_drift = p_val < 0.05

                    if is_drift:
                        drift_count += 1

                    explanation = DRIFT_EXPLANATIONS.get(col, f"Feature {col} distribution shifted from training baseline.")

                    results.append({
                        "feature": col,
                        "drift_detected": is_drift,
                        "metric_type": "KS",
                        "metric_value": round(ks_stat, 4),
                        "p_value": round(p_val, 4),
                        "threshold": "p < 0.05",
                        "explanation": explanation if is_drift else "Distribution matches training baseline."
                    })

        # 2. Evaluate Categorical/One-Hot Features (PSI)
        for col, meta in categorical_baseline.items():
            if col in prod_df.columns and len(prod_df) >= 5:
                exp_prop = meta.get("proportion", 0.1)
                act_prop = float(prod_df[col].mean()) if len(prod_df) > 0 else exp_prop
                psi_val = self.calculate_psi(exp_prop, act_prop)
                is_drift = psi_val > 0.2

                if is_drift:
                    drift_count += 1

                explanation = DRIFT_EXPLANATIONS.get(col, f"Category proportion for {col} shifted significantly.")

                results.append({
                    "feature": col,
                    "drift_detected": is_drift,
                    "metric_type": "PSI",
                    "metric_value": round(psi_val, 4),
                    "threshold": "PSI > 0.2",
                    "explanation": explanation if is_drift else "Category proportion stable."
                })

        overall_status = "DRIFT_DETECTED" if drift_count > 0 else "STABLE"

        return {
            "checked_at": datetime.utcnow().isoformat(),
            "window_size": len(prod_df),
            "drift_feature_count": drift_count,
            "overall_status": overall_status,
            "features": results
        }

drift_service = DriftService()
