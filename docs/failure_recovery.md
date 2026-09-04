# Failure Recovery Log

This document captures the real engineering problems encountered during development, why they happened, and exactly what changed. This is not a polished post-mortem — it is a live record written as issues were identified and resolved.

---

## Failure 1 — Label/Feature Circularity (`prior_low_review_count`)

**What broke:**
`prior_low_review_count` was included in the model's feature set (`features.py`) while simultaneously being one of three OR-conditions that define the `return_risk = 1` label in `labeling.py`:

```python
rule_prior_reviews = df["prior_low_review_count"] >= p_thresh
df["return_risk"] = (rule_low_review | rule_delay | rule_prior_reviews).astype(int)
```

This created definitional overlap: XGBoost could trivially threshold this single column to correctly classify ~⅓ of all positive-class examples without learning any genuine return-risk signal. Reported precision/recall on those rows was partly measuring "did the model rediscover the labeling rule," not predictive ability.

**Why it happened:**
The feature is temporally valid — it is an expanding count of prior low reviews, strictly computed before the current order using `.shift(1).cumsum()`, so there is no time-leakage. The problem is not temporal; it is definitional. Past behavior predicting future behavior is legitimate. Past behavior *defining* the label and then being fed back as a feature is not.

**What changed:**
- `prior_low_review_count` removed from `feature_cols` in [`ml/src/features.py`](../ml/src/features.py).
- A comment explaining the exact reason is written inline at the removal point for future contributors.
- Full pipeline retrained: `features → train → baselines → calibration → cost_model → evaluate`.
- The field is still sent in the API payload (with a fixed default of `0`) so the backend schema remains stable, but it is no longer exposed in the UI.
- The field is no longer shown in the assessment form in [`frontend/src/pages/AssessmentPage.jsx`](../frontend/src/pages/AssessmentPage.jsx).

**Honest impact:**
Savings vs. Flag Nothing dropped from ₹954,000 → ₹89,000. ROC-AUC dropped to 0.5536. This is the correct result. The model now has to earn its metrics through the remaining features (order value, freight, payment type, installments, address mismatch, product category, customer order count). The dataset (Olist) has limited at-placement signal; a real Razorpay deployment would have richer features.

---

## Failure 2 — F1 Threshold Swept on Test Set (`evaluate.py`)

**What broke:**
The F1-optimal threshold comparison in `evaluate.py` was computed by sweeping thresholds against `y_test` / `y_prob` — the held-out test set. This directly contradicts the project's own principle that thresholds are selected on the validation set and measured on the test set.

The cost-optimal and constrained thresholds were both correctly selected on `val_features.csv`. The F1 comparison baseline was not, making the evaluation internally inconsistent.

**Why it happened:**
The code comment at the time read *"re-swept on validation / train for comparison, or here for local reference"* — an acknowledged workaround that was never corrected before submission.

**What changed:**
- `evaluate.py` now loads `val_features.csv`, computes `y_prob_val`, and sweeps F1 on the validation distribution.
- The val-selected `f1_opt_thresh` is then applied to `y_test` for final reporting — exactly matching how the cost-optimal and constrained thresholds work.
- The conclusion (cost-optimal saves more than F1-optimal) is unchanged. The fix closes an inconsistency a careful reader would find.

---

## Failure 3 — Dead Input Fields in Live Demo UI

**What broke:**
Two input fields in the assessment form (`delivery_delay_days` and `prior_low_review_count`) were displayed as labeled, required, editable inputs that appeared to drive the risk score. Neither affected scoring:

- `delivery_delay_days` is accepted by the backend schema but silently dropped before inference — it is not in `feature_cols` and never was.
- `prior_low_review_count` was removed from `feature_cols` by Failure 1's fix above.

A judge who changed either slider during a live demo would see the score not move — the worst possible moment for an unexplained behavior.

**Why it happened:**
`delivery_delay_days` was retained in the API schema intentionally ("to avoid breaking recorded video demonstrations" — acknowledged in the original docs). `prior_low_review_count` became inert after the circularity fix and the frontend was not updated in the same commit.

**What changed:**
- Both fields removed from `FIELD_META` in `AssessmentPage.jsx` — they are no longer rendered in the UI.
- Both fields still sent in the API payload with fixed defaults (`delivery_delay_days: 0.0`, `prior_low_review_count: 0`) so the backend schema doesn't break.
- Preset scenarios (`fillHigh`, `fillLow`) cleaned of the removed fields.
- Comments in `AssessmentPage.jsx` explain exactly why each field is inert, for the next person who reads the code.

---

## What This Demonstrates

These three failures were found, documented, and fixed before submission — not after. The metrics are lower as a result. That is the point: an honest metric that reflects real signal is more useful than an inflated metric that partially measures a labeling artifact. The methodology (cost-based threshold selection on validation set, no test-set leakage, SHAP explainability) remains valid and is now also internally consistent.

The underlying dataset limitation — Olist is Brazilian e-commerce; at-placement features carry limited RTO signal — is real and would be addressed in a production deployment with Razorpay's richer transaction and merchant history features.
