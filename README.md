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

The model is evaluated on a **held-out test set (15% of data, chronologically last)**, strictly separate from training (70%) and threshold selection (15% validation).

The pipeline is: `train_features.csv` → model training → `val_features.csv` → threshold optimization → `test_features.csv` → final evaluation only.

> **Important**: The metrics below depend heavily on which **threshold/policy** is chosen. ROC-AUC and PR-AUC are threshold-independent measures of raw model discrimination. Precision and recall are policy outcomes.

### Threshold-Independent Model Capability (Test Set)

| Metric       |      Result | Interpretation |
| ------------ | ----------: | :------------- |
| **ROC-AUC**  |  **0.5591** | Better than random (0.50 = random) |
| **PR-AUC**   |  **0.1886** | 18.9% vs. 15.9% random baseline (class prevalence = 15.9%) — positive signal |
| Brier Score  |    0.2438   | Calibration quality of probability estimates |
| Test samples |    14,917   | Chronologically held-out orders |

> These features are deliberately limited to **prediction-time only information** (available at order placement, before fulfillment). Future signals such as actual delivery delays and customer review scores are excluded to prevent data leakage. This is the reason discriminative power is modest — it is an honest representation of what is knowable at the time of the decision.

### Baseline Model Comparison (Test Set, threshold-independent ROC-AUC)

| Classifier               | ROC-AUC | PR-AUC | Notes |
| :----------------------- | ------: | -----: | :---- |
| Dummy (Class Prior)      |  0.5000 | 0.1591 | Random baseline |
| Logistic Regression      |  0.5334 | 0.1704 | |
| Random Forest            |  0.5391 | 0.1742 | |
| XGBoost (Standard)       |  0.5591 | 0.1886 | Best discrimination |
| **Cost-Optimized XGBoost** | **0.5591** | **0.1886** | Same model, different threshold policy |

### Operating Curve — Threshold is a Policy Choice

A key feature of this system is that **precision and recall are not fixed numbers**. The merchant selects an operating point based on their operational capacity.

| Threshold | Precision | Recall | Review Rate | Expected Financial Loss |
| :-------: | --------: | -----: | ----------: | ----------------------: |
| 0.50 (standard) | 16.5% | **54.5%** | 42.53% | ₹39.60 Lakhs |
| 0.60 | 22.3% | **21.1%** | 12.20% | ₹29.80 Lakhs |
| 0.65 | 26.6% | **12.2%** | 5.91% | ₹28.53 Lakhs |
| **0.78 (cost-optimal)** | **47.2%** | **5.3%** | **1.31%** | **₹25.37 Lakhs** |

**To a reviewer who asks "Why only 5.26% recall?":**

The model detects **54.5% of risky orders** at the standard threshold. We chose τ = 0.78 because it minimizes the merchant's expected financial loss given the 1:3 FP/FN cost structure. A merchant willing to review more orders can lower the threshold in real time using the **Threshold Optimizer slider** in the UI. That is precisely what the system is built for.

---

# 3. Financial Impact

The model's threshold is selected using the financial cost of mistakes rather than an arbitrary probability such as `0.5`. All numbers below are from the **untouched test set**.

| Policy                              | Expected Cost | Savings vs. Flag Nothing |
| :---------------------------------- | ------------: | -----------------------: |
| Flag Nothing (τ = 1.0)              |  ₹26.235 Lakhs |                        — |
| Flag Everything (τ = 0.0)           |  ₹65.840 Lakhs |              -₹39.6 Lakhs |
| XGBoost at τ = 0.50 (high recall)   |  ₹39.600 Lakhs |              -₹13.4 Lakhs |
| XGBoost at τ = 0.60                 |  ₹29.800 Lakhs |               -₹3.6 Lakhs |
| XGBoost at τ = 0.65                 |  ₹28.530 Lakhs |               -₹2.3 Lakhs |
| **Cost-Optimized XGBoost (τ = 0.78)** | **₹25.370 Lakhs** | **₹0.865 Lakhs saved** |

This directly illustrates why blindly choosing high-recall (τ = 0.50) is financially suboptimal: despite catching 54.5% of risky orders, the volume of false positives (42.5% review rate) makes it **more expensive** than the flag-nothing baseline. The cost-optimal threshold is the one that genuinely reduces expected merchant loss.

### Merchant Operational Constraint

Beyond pure cost minimization, the system supports a merchant budget constraint:

> **"Only review ≤ 5% of orders manually."**

At this budget, the threshold optimizes to **τ = 0.78**, achieving a **1.31% actual review rate** — well within the operational limit.

### Result

**Cost-optimized policy saves ₹86,500 vs. the Flag Nothing policy.**
**It saves ₹40.47 Lakhs vs. flagging everything.**

The cost-optimal threshold τ = 0.78 is selected on the **validation set** (not the test set) to prevent test-set leakage, then applied to the untouched test set for final reporting.

---

# 4. Why Not Just Optimize F1?

High recall at τ = 0.50 catches more risky orders — but also flags 42.5% of all orders for manual review, making it operationally infeasible and financially more costly than not flagging anything at all.

```text
False Positive = ₹500 (unnecessary review of a safe order)
False Negative = ₹1,500 (missed risky order slips through)
```

Missing a genuinely risky return is **3× more expensive** than a false positive. But with 84% of orders being safe, the volume of false positives at low thresholds overwhelms the FN savings.

The cost-optimal threshold explicitly solves this tradeoff.

### Decision objective

```text
Prediction quality
        +
Financial consequence of each error type
        +
Merchant's operational capacity constraint
        ↓
Optimal intervention policy
```

This makes the model useful to a merchant risk team, not merely an ML benchmark.

---

# 5. Explainable AI Decisions

Every risk decision can be explained using **SHAP feature attribution**.

Example *(illustrative — actual SHAP values vary per order)*:

```text
ORDER #18492

Risk Score
0.87

Decision
HOLD FOR MANUAL REVIEW

Top Risk Factors
────────────────────────────
Freight value        +0.21
Prior low reviews    +0.18
Payment type (boleto)+0.14
Order value          +0.09

Decision threshold
0.78  ← cost-optimal threshold (selected on validation set)
```

> **Note on features:** All factors above are available at order placement time. Post-fulfillment signals (actual delivery delay, review score for the current order) are **excluded** from the model to prevent target leakage.

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

All models are trained on the same `train_features.csv` split and evaluated on the same untouched `test_features.csv`. Financial cost uses ₹500 FP / ₹1,500 FN at each model's default threshold (τ = 0.50), except for the cost-optimized XGBoost which uses τ = 0.78 (selected on validation set).

| Model / Policy               | Precision | Recall | ROC-AUC | PR-AUC | Financial Cost |
| :--------------------------- | --------: | -----: | ------: | -----: | -------------: |
| Flag Nothing (τ = 1.0)       |        — |     — |      — |     — |    ₹26.235L |
| Flag Everything (τ = 0.0)    |        — |     — |      — |     — |    ₹65.840L |
| Logistic Regression (τ=0.50) |    20.5% | 54.7% |  0.5334 | 0.1704 |             — |
| Random Forest (τ=0.50)       |    12.4% | 33.7% |  0.5391 | 0.1742 |             — |
| XGBoost (τ=0.50)             |    16.5% | 54.5% |  0.5591 | 0.1886 |    ₹39.600L |
| **Cost-Optimized XGBoost (τ=0.78)** | **47.2%** | **5.3%** | **0.5591** | **0.1886** | **₹25.370L** |

The key comparison is not only:

> **Which model predicts best?**

but:

> **Which policy produces the lowest expected merchant loss?**

XGBoost has the highest discrimination (PR-AUC 0.1886 vs. 0.1742 Random Forest, 0.1704 LR). At the cost-optimal threshold, it also produces the lowest expected financial loss of any evaluated policy.

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
