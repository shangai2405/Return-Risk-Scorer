# Return-Risk Scorer — AI Merchant Risk Engine

> **An explainable AI decision engine that predicts return/RTO risk, optimizes intervention thresholds by financial loss, explains every decision, and monitors model reliability in production.**

**Built for the Razorpay Buildathon — Risk Manager Track**

---

## The Problem

Returns and Return-to-Origin (RTO) orders create a compound loss for merchants:

* Reverse logistics costs
* Product loss and restocking costs
* Customer-support workload
* Manual review overhead
* Payment/dispute-related operational costs

A conventional classifier answers:

> **"How accurately can we predict a return?"**

A risk manager needs to answer:

> **"Which orders should we actually intervene on, and what decision minimizes the merchant's financial loss?"**

**Return-Risk Scorer is designed around the second question.**

---

# What the System Does

For every incoming order, the engine produces:

```text
Order
  ↓
Feature extraction
  ↓
AI return-risk prediction
  ↓
Cost-sensitive decision threshold
  ↓
┌─────────────────────────────┐
│ AUTO-APPROVE                │
│ or                          │
│ HOLD FOR MANUAL REVIEW      │
└─────────────────────────────┘
  ↓
SHAP explanation
  ↓
Audit record
```

At the same time, a separate monitoring layer checks whether production data has drifted away from the training distribution.

So the system isn't just a **risk model**.

It is:

> **Prediction + Decision Optimization + Explainability + Monitoring + Human Oversight**

---

# Why This Is Different

Most return-risk systems stop at:

```text
XGBoost → probability → threshold
```

This project treats risk scoring as an **economic decision problem**.

### 1. Cost-sensitive threshold optimization

False positives and false negatives have different financial consequences.

We explicitly model:

* **False Positive:** ₹500

  * unnecessary manual review
  * support/operations cost
  * customer friction

* **False Negative:** ₹1,500

  * missed high-risk return
  * reverse logistics
  * restocking/product loss
  * dispute-related costs

The production threshold is therefore selected by minimizing expected financial loss:

$$\
\tau^\* =\
\arg\min\_\tau\
\left(\
FP(\tau)\times500 +\
FN(\tau)\times1500\
\right)\
$$

This is fundamentally different from blindly optimizing Accuracy or F1.

---

# 2. Held-Out Model Evaluation

The model is evaluated on a **held-out test set**, separate from training and threshold selection.

### Test-set performance

| Metric       |                    Result |
| ------------ | ------------------------: |
| Precision    | **[INSERT ACTUAL VALUE]** |
| Recall       | **[INSERT ACTUAL VALUE]** |
| F1 Score     | **[INSERT ACTUAL VALUE]** |
| ROC-AUC      | **[INSERT ACTUAL VALUE]** |
| Test samples | **[INSERT ACTUAL VALUE]** |

> **Do not replace these values with training metrics. These numbers should come directly from the final evaluation pipeline.**

### Why both Precision and Recall matter

A high-recall system catches more risky returns but may send too many legitimate orders to manual review.

A high-precision system reduces unnecessary interventions but may allow costly risky orders through.

The system therefore separates:

**Model quality**

from

**Business decision quality**

---

# 3. Financial Impact

The model's threshold is selected using the financial cost of mistakes rather than an arbitrary probability such as `0.5`.

Current evaluation:

| Policy                   |     Expected Cost |
| ------------------------ | ----------------: |
| Flag Nothing             |     ₹34.335 Lakhs |
| Flag Everything          |     ₹88.000 Lakhs |
| **Cost-Optimized Model** | **₹24.795 Lakhs** |

### Result

**Cost-optimized policy saves approximately ₹9.54 Lakhs vs. flagging nothing.**

It saves approximately:

**₹63.21 Lakhs vs. flagging everything.**

The current cost-optimal threshold is:

```text
τ = 0.75
```

This threshold is selected because it minimizes the modeled financial loss under the defined FP/FN costs.

---

# 4. Why Not Just Optimize F1?

Suppose two models have similar F1 scores.

That does **not** mean they have the same financial impact.

Consider:

```text
False Positive = ₹500
False Negative = ₹1,500
```

Missing a genuinely risky return is therefore **3× more expensive** than unnecessarily reviewing a safe order.

The system explicitly captures this asymmetry.

### Decision objective

```text
Prediction quality
        +
Financial consequence
        ↓
Operational decision
```

This makes the model useful to a merchant risk team rather than only to an ML benchmark.

---

# 5. Explainable AI Decisions

Every risk decision can be explained using **SHAP feature attribution**.

Example:

```text
ORDER #18492

Risk Score
0.87

Decision
HOLD FOR MANUAL REVIEW

Top Risk Factors
────────────────────────────
Delivery delay       +0.24
Previous returns     +0.18
Review behaviour     +0.13
Payment behaviour    +0.09

Decision threshold
0.75
```

The goal is not simply to say:

> "The model thinks this order is risky."

It is to answer:

> **"Why did the model think this order was risky?"**

This creates an auditable decision trail for analysts and risk operations.

---

# 6. Human-in-the-Loop Risk Management

The system does not assume that the model is always correct.

Analysts can review model decisions and their decisions can be compared with model outputs.

This produces an **analyst-agreement signal**:

```text
Model decision
      ↓
Analyst review
      ↓
Agreement / Disagreement
      ↓
Risk segment analysis
```

This allows teams to identify areas where:

* the model is consistently aligned with analysts
* analysts frequently override the model
* certain customer/order segments require additional investigation

The objective is to make AI a **decision-support system**, not an opaque replacement for risk operations.

---

# 7. Production Drift Monitoring

A model that performs well today can degrade when production behaviour changes.

The system therefore includes an independent statistical monitoring layer.

### Numerical features

Uses the **two-sample Kolmogorov-Smirnov test**.

```text
p-value < 0.05
        ↓
DRIFT DETECTED
```

### Categorical features

Uses **Population Stability Index (PSI)**.

```text
PSI > 0.20
      ↓
DRIFT DETECTED
```

The monitoring layer compares production distributions against the training baseline.

### Important design decision

Drift monitoring is deliberately **out-of-band**.

It does not silently modify:

* model weights
* scoring logic
* risk thresholds

Instead, it surfaces a warning to risk operators.

This prevents an automated monitoring component from unexpectedly changing production decisions.

---

# 8. Empirical Label Construction

The target label is not based on arbitrary hardcoded assumptions.

The labeling pipeline first examines the empirical distribution of the dataset and stores the resulting parameters in:

```text
ml/artifacts/labeling_thresholds.json
```

Current derived parameters include:

```text
Delivery-delay cutoff:
90th percentile → 4 days

Prior low-review threshold:
2

Review-score threshold:
2
```

The same generated parameters are then reused when constructing the final labeled dataset.

This creates a reproducible **single source of truth** between:

```text
Label generation
      ↓
Model training
      ↓
Evaluation
```

---

# 9. Baseline Comparison

The system should be evaluated against simpler alternatives rather than presenting XGBoost in isolation.

Recommended comparison:

| Model / Policy             | Precision | Recall |    F1 | Financial Cost |
| -------------------------- | --------: | -----: | ----: | -------------: |
| Flag Nothing               |         — |      — |     — |       ₹34.335L |
| Flag Everything            |         — |      — |     — |       ₹88.000L |
| Logistic Regression        |         — |      — |     — |              — |
| Random Forest              |         — |      — |     — |              — |
| XGBoost                    |         — |      — |     — |              — |
| **Cost-Optimized XGBoost** |     **—** |  **—** | **—** |   **₹24.795L** |

The key comparison is not only:

> **Which model predicts best?**

but:

> **Which policy produces the lowest expected merchant loss?**

---

# 10. System Architecture

```text
                    ┌────────────────────┐
                    │     Order Data     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Feature Engineering│
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ XGBoost Risk Model │
                    └─────────┬──────────┘
                              │
                       Risk Probability
                              │
                              ▼
                    ┌────────────────────┐
                    │ Cost Optimization  │
                    │    Threshold       │
                    └─────────┬──────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          AUTO-APPROVE              HOLD / REVIEW
                 │                         │
                 └────────────┬────────────┘
                              ▼
                    ┌────────────────────┐
                    │   SHAP Explainability│
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  Audit / Analyst   │
                    │      Feedback      │
                    └────────────────────┘


       ┌──────────────────────────────────────────┐
       │         Independent Monitoring Layer     │
       │                                          │
       │  Training Baseline ↔ Production Data    │
       │       │                                  │
       │       ├── KS Test                       │
       │       └── PSI                           │
       │                                          │
       │              ↓                           │
       │        Drift Alert                      │
       └──────────────────────────────────────────┘
```

---

# 11. Technology Stack

### Machine Learning

* Python
* XGBoost
* Scikit-learn
* SHAP
* Pandas
* NumPy
* SciPy

### Backend

* FastAPI
* Uvicorn

### Frontend

* React
* Vite

### Monitoring

* Kolmogorov-Smirnov Test
* Population Stability Index
* Distribution baselines

---

# 12. Project Structure

```text
Return-Risk-Scorer/
│
├── backend/
│   └── app/
│
├── frontend/
│
├── ml/
│   ├── src/
│   │   ├── labeling.py
│   │   ├── features.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── cost_model.py
│   │   ├── cost_sensitivity.py
│   │   └── drift_baseline.py
│   │
│   └── artifacts/
│
├── docs/
│
├── requirements.txt
└── README.md
```

---

# 13. Quick Start

## Prerequisites

* Python 3.10+
* Node.js 18+
* npm
* OpenMP

On macOS:

```bash
brew install libomp
```

## Run the ML pipeline

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/labeling.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/features.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/train.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/drift_baseline.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/cost_model.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/cost_sensitivity.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/evaluate.py
```

## Start the backend

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib \
PYTHONPATH=. \
uvicorn backend.app.main:app --port 8000 --reload
```

## Start the frontend

```bash
cd frontend
npm run dev
```

Application:

```text
http://localhost:5173
```

API documentation:

```text
http://localhost:8000/docs
```

---

# 14. Buildathon Fit — Razorpay Risk Manager

This project targets the **Risk Manager** problem:

> Prevent merchants from losing money to risky returns/RTO orders.

The system demonstrates the complete risk-management loop:

```text
DETECT
Identify potentially risky orders.

↓

DECIDE
Choose whether to approve or hold based on
financially optimized risk thresholds.

↓

EXPLAIN
Show why the order received its risk score.

↓

MONITOR
Detect production distribution shifts.

↓

REVIEW
Track analyst decisions and model agreement.

↓

AUDIT
Preserve transparent decision information.
```

The key design principle is:

> **Don't optimize a model in isolation. Optimize the merchant's risk decision.**

---

# 15. What Makes It Production-Oriented?

A production risk system needs more than a classifier.

This project addresses five layers:

| Layer           | Implementation                        |
| --------------- | ------------------------------------- |
| Prediction      | XGBoost                               |
| Decision        | Cost-sensitive threshold optimization |
| Explainability  | SHAP                                  |
| Reliability     | KS + PSI drift monitoring             |
| Human Oversight | Analyst agreement tracking            |

This transforms the project from a standalone ML model into an **end-to-end risk decision engine**.

---

# 16. Limitations & Next Steps

The current implementation is a research/prototype system built around the available dataset.

Production deployment would require:

* live merchant/order integrations
* real-time feature pipelines
* calibrated probabilities
* larger temporal validation sets
* merchant-specific cost parameters
* online monitoring infrastructure
* model retraining policies
* additional fraud/abuse signals
* A/B testing of intervention strategies

These are deployment considerations rather than assumptions hidden inside the current model.

---

# 17. Core Takeaway

Most ML systems ask:

> **"Can we predict risk?"**

Return-Risk Scorer asks a more useful question:

> **"Given the cost of being wrong, what should the merchant do?"**

It combines:

**AI prediction**

* **financial optimization**

* **explainability**

* **drift detection**

* **human oversight**

to create an **audit-ready return-risk decision engine for merchants.**

---

## Built For

**Razorpay Buildathon — Risk Manager**

**Problem focus:** Return / RTO loss prevention

**Core objective:** Minimize merchant loss while maintaining measurable model performance and operational transparency.
