# Failure Recovery Log

This document captures the real engineering problems encountered during development, why they happened, and exactly what changed. This is not a polished post-mortem — it is a live record written as issues were identified and resolved.

---

## Failure 1 — Label/Feature Circularity (`prior_low_review_count`)

**What broke:**
The original label was a three-condition OR:

```python
rule_low_review    = df["review_score"] <= 2
rule_delay         = df["delivery_delay_days"] > 4
rule_prior_reviews = df["prior_low_review_count"] >= 2
df["return_risk"]  = (rule_low_review | rule_delay | rule_prior_reviews).astype(int)
```

`prior_low_review_count` was included in `features.py` as a model input while simultaneously being one of the three conditions that defined `return_risk = 1`. XGBoost could trivially threshold this single column to correctly classify ~⅓ of all positive-class examples without learning any genuine return-risk signal.

**Why it happened:**
The feature is temporally valid (expanding prior count, `.shift(1).cumsum()`, no time-leakage). The problem is definitional, not temporal.

**What changed — iterative fix:**

*First iteration (insufficient):* Removed `prior_low_review_count` from `feature_cols`. This fixed the circularity but caused ROC-AUC to drop to 0.5536 (near-random), confirming the feature was carrying substantial signal that the remaining features could not replicate.

*Final resolution:* Changed the label definition to a **single criterion** — `return_risk = 1` iff `review_score <= 2` — and restored `prior_low_review_count` as a legitimate feature:
- `review_score <= 2` is a single, interpretable proxy: the model now predicts one statable thing ("will this order result in explicit customer dissatisfaction?")
- `prior_low_review_count` is now a pure predictor — past low-review behaviour predicting future dissatisfaction is valid signal; it was only circular when it also defined the label
- `delivery_delay_days` stays out of both label and features — it is a post-fulfillment signal unknowable at prediction time
- Model after fix: ROC-AUC **0.5666**, PR-AUC **0.1826** (up from 0.5536 / 0.1749 in the intermediate state)

**Honest impact:**
Savings vs. Flag Nothing is ₹88,000 on the 14,917-order test set. The construct validity is clean: the model predicts a single, statable thing, and every feature is a genuine predictor of that thing.

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
