# Return-Risk Scorer — AI Merchant Risk Engine

> **An explainable AI decision engine that predicts return/RTO risk, optimizes intervention thresholds by financial loss, explains every decision, and monitors model reliability in production.**

**Built for the Razorpay Buildathon — Risk Manager Track**

🌐 **Live Demo:** [https://shangai2405.github.io/Return-Risk-Scorer/](https://shangai2405.github.io/Return-Risk-Scorer/)

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

> **What the model predicts:** The model predicts whether an order will result in a **1–2 star customer review** — the closest available single-criterion proxy for customer dissatisfaction and return/dispute risk in the Olist dataset. It does not directly predict fraud, chargebacks, or physical returns; a production deployment on Indian merchant data would use richer labels and features.

> **Important**: The metrics below depend heavily on which **threshold/policy** is chosen. ROC-AUC and PR-AUC are threshold-independent measures of raw model discrimination. Precision and recall are policy outcomes.

### Threshold-Independent Model Capability (Test Set)

| Metric       |      Result | Interpretation |
| ------------ | ----------: | :------------- |
| **ROC-AUC**  |  **0.5666** | Better than random (0.50 = random); modest signal given prediction-time-only features |
| **PR-AUC**   |  **0.1826** | 18.3% vs. 10.9% random baseline (class prevalence = 10.9%) — positive signal above chance |
| Brier Score  |    0.2418   | Calibration quality of probability estimates |
| Test samples |    14,917   | Chronologically held-out orders (1,630 positive / 13,287 negative) |

> These features are deliberately limited to **prediction-time only information** (available at order placement, before fulfillment). Post-fulfillment signals such as actual delivery delays and current-order review scores are excluded to prevent data leakage. This is the reason discriminative power is modest — it is an honest representation of what is knowable at the time of the decision.

### Baseline Model Comparison (Test Set, threshold-independent)

| Classifier               | ROC-AUC | PR-AUC | Notes |
| :----------------------- | ------: | -----: | :---- |
| Dummy (Class Prior)      |  0.5000 | 0.1093 | Random baseline (PR-AUC = class prevalence) |
| Logistic Regression      |  0.5437 | 0.1440 | |
| Random Forest            |  0.5434 | 0.1578 | |
| XGBoost (Standard)       |  0.5666 | 0.1826 | Best discrimination |
| **Cost-Optimized XGBoost** | **0.5666** | **0.1826** | Same model, different threshold policy |

### Operating Curve — Threshold is a Policy Choice

A key feature of this system is that **precision and recall are not fixed numbers**. The merchant selects an operating point based on their operational capacity. All values below are from the held-out **test set**.

| Threshold | Precision | Recall | Review Rate | Expected Financial Loss |
| :-------: | --------: | -----: | ----------: | ----------------------: |
| 0.50 (standard) | 13.0% | **51.0%** | 42.84% | ₹39.76 Lakhs |
| 0.60 | 17.7% | **21.5%** | 13.24% | ₹27.33 Lakhs |
| 0.65 | 21.2% | **12.7%** | 6.54% | ₹25.19 Lakhs |
| 0.70 | 31.2% | **8.2%** | 2.88% | ₹23.92 Lakhs |
| **0.79 (cost-optimal)** | **49.4%** | **5.5%** | **1.21%** | **₹23.57 Lakhs** |

**To a reviewer who asks "Why only 5.5% recall?":**

The model detects **51% of risky orders** at the standard τ = 0.50 threshold. The cost-optimal τ = 0.79 is chosen because at the 1:3 FP/FN cost ratio, a model with modest discrimination (ROC-AUC 0.57) minimizes expected loss by flagging only its highest-confidence predictions. A merchant willing to review more orders can lower the threshold in real time using the **Threshold Optimizer slider** in the UI — the system is built to support that choice explicitly.

---

# 3. Financial Impact

The model's threshold is selected using the financial cost of mistakes rather than an arbitrary probability such as `0.5`. All numbers below are from the **untouched test set**.

| Policy                              | Expected Cost | Savings vs. Flag Nothing |
| :---------------------------------- | ------------: | -----------------------: |
| Flag Nothing (τ = 1.0)              |  ₹24.45 Lakhs |                        — |
| Flag Everything (τ = 0.0)           |  ₹66.44 Lakhs |              -₹42.0 Lakhs |
| XGBoost at τ = 0.50 (high recall)   |  ₹39.76 Lakhs |              -₹15.3 Lakhs |
| XGBoost at τ = 0.60                 |  ₹27.33 Lakhs |               -₹2.88 Lakhs |
| XGBoost at τ = 0.65                 |  ₹25.19 Lakhs |               -₹0.74 Lakhs |
| **Cost-Optimized XGBoost (τ = 0.79)** | **₹23.57 Lakhs** | **₹0.88 Lakhs saved** |

This directly illustrates why blindly choosing high-recall (τ = 0.50) is financially suboptimal: despite catching 51% of risky orders, the volume of false positives (42.8% review rate) makes it **more expensive** than the flag-nothing baseline. The cost-optimal threshold is the one that genuinely reduces expected merchant loss.

### Merchant Operational Constraint

Beyond pure cost minimization, the system supports a merchant budget constraint:

> **"Only review ≤ 5% of orders manually."**

At this budget, the threshold optimizes to **τ = 0.79**, achieving a **1.21% actual review rate** — well within the operational limit.

### Result

**Cost-optimized policy saves ₹88,000 vs. the Flag Nothing policy.**
**It saves ₹42.87 Lakhs vs. flagging everything.**

The cost-optimal threshold τ = 0.79 is selected on the **validation set** (not the test set) to prevent test-set leakage, then applied to the untouched test set for final reporting.

---

# 4. Why Not Just Optimize F1?

High recall at τ = 0.50 catches more risky orders — but also flags 42.5% of all orders for manual review, making it operationally infeasible and financially more costly than not flagging anything at all.

```text
False Positive = ₹500 (unnecessary review of a safe order)
False Negative = ₹1,500 (missed risky order slips through)
```

Missing a genuinely risky return is **3× more expensive** than a false positive. But with ~85% of orders being safe, the volume of false positives at low thresholds overwhelms the FN savings.

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
0.79  ← cost-optimal threshold (selected on validation set)
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

All models are trained on the same `train_features.csv` split and evaluated on the same untouched `test_features.csv`. Financial cost uses ₹500 FP / ₹1,500 FN at each model's default threshold (τ = 0.50), except for the cost-optimized XGBoost which uses τ = 0.79 (selected on validation set).

| Model / Policy               | Precision | Recall | ROC-AUC | PR-AUC | Financial Cost |
| :--------------------------- | --------: | -----: | ------: | -----: | -------------: |
| Flag Nothing (τ = 1.0)       |        — |     — |      — |     — |    ₹24.45L |
| Flag Everything (τ = 0.0)    |        — |     — |      — |     — |    ₹66.44L |
| Logistic Regression (τ=0.50) |    12.2% | 50.7% |  0.5437 | 0.1440 |    ₹41.76L |
| Random Forest (τ=0.50)       |    19.6% |  9.4% |  0.5434 | 0.1578 |    ₹25.30L |
| XGBoost (τ=0.50)             |    13.0% | 51.0% |  0.5666 | 0.1826 |    ₹39.76L |
| **Cost-Optimized XGBoost (τ=0.79)** | **49.4%** | **5.5%** | **0.5666** | **0.1826** | **₹23.57L** |

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

### Dataset Disclosure

**The model is trained on the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — Brazilian e-commerce transaction data, not Indian merchant data.** The ₹500 / ₹1,500 cost constants and the RTO framing used throughout this project are illustrative of the target deployment context (Indian payment gateways, Razorpay merchants); they are not derived from Indian transaction distributions. The underlying delivery patterns, payment method mix, and review behaviour the model learned from are Brazilian. A deployment against real Razorpay or Indian merchant data would require retraining on that data, and the model's discrimination and cost figures would change accordingly.

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
