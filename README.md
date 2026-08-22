#  Return-Risk Scorer — Enterprise Risk Engine (Indian BFSI & E-Commerce)

> **Audit-Ready Explainable Return-Risk Scoring Engine with Cost-Based Threshold Optimization, Statistical Drift Monitoring, and Analyst Agreement Tracking**

---

##  Indian BFSI & Fintech Alignment

This system directly hits key risk challenges faced by **Indian BFSI, Payment Gateways (Razorpay, Paytm, Cashfree, PhonePe), and E-Commerce Platforms**:

1. **RTO (Return to Origin) & Logistics Risk**: High freight costs and delivery delays in India lead to massive Return-To-Origin (RTO) financial losses.
2. **Payment Method Risk Profiling**: Differentiates risk between instant digital payments vs. deferred/voucher payment instruments (Boleto/COD).
3. **Dispute & Support Overhead**: Minimizes manual ops review costs (₹500/ticket) while shielding merchants from product loss and chargebacks (₹1,500/order).

---

##  Empirical Percentile-Based Labeling Methodology

Rather than assuming hardcoded guesses (such as a fixed 7 days or 3 complaints), our labeling pipeline computes empirical distributions directly from the dataset before applying the target rule, saving the exact configuration to `ml/artifacts/labeling_thresholds.json`:

```json
{
  "delay_threshold_days": 4,
  "delay_percentile_used": 90,
  "prior_low_review_threshold": 2,
  "prior_low_review_rationale": "smallest value where <10% of repeat customers exceed it",
  "review_score_threshold": 2,
  "review_score_rationale": "Olist's own rating scale treats 1-2 as explicit dissatisfaction"
}
```

### Key Empirical Takeaways:
- **Delivery Delay Threshold**: The 90th percentile delivery delay across all orders was evaluated at **4 days** (relative to estimated delivery date). `delivery_delay_days > 4` is set as the operational delay cutoff.
- **Prior Low-Review Threshold**: Among repeat customers, $\ge 2$ represents the smallest integer value where fewer than $10\%$ ($<1.0\%$) of repeat customers exceed it.
- **Single Source of Truth**: `labeling.py` computes and writes `labeling_thresholds.json`, then reads these exact parameters back in when constructing `labeled_orders.csv`.

---

##  Statistical Data Drift Monitoring (Pure Statistics — No LLM)

Detects when production order feature distributions deviate from the training baseline before precision/recall silently degrade in the field:

- **Two-Sample Kolmogorov-Smirnov (KS) Test (Numeric Features)**: Evaluates `scipy.stats.ks_2samp` against training set baseline sample ($N = 1000$). Flags feature as drifted if $p\text{-value} < 0.05$.
- **Population Stability Index (PSI) (Categorical Features)**: Measures structural category shifts:
  $$\text{PSI} = \sum \left( A_i - E_i \right) \times \ln\left(\frac{A_i}{E_i}\right)$$
  Flags feature as drifted if $\text{PSI} > 0.2$ (industry standard threshold).
- **Out-of-Band Risk Control**: Read-only endpoint (`GET /drift-status`) and dashboard panel (`DriftPanel.jsx`) that **never touches scoring or thresholding logic**.

---

##  Honest Metrics (Factoring False-Positive Costs)

Unlike standard machine learning projects that optimize for abstract F1-scores or Accuracy (ignoring operational expenses), this system delivers **honest financial metrics**:

- **False-Positive Cost ($C_{\text{FP}} = ₹500$)**: Explicitly factors in the ₹500 penalty of unnecessarily flagging a safe order for manual check (support staff labor + customer friction).
- **False-Negative Cost ($C_{\text{FN}} = ₹1,500$)**: Factors in the ₹1,500 penalty of missing a bad return order (reverse shipping + restock loss + dispute fees).
- **Mathematical Loss Objective**:
  $$\tau^* = \arg\min_{\tau} \left( \text{FP}(\tau) \times 500 + \text{FN}(\tau) \times 1500 \right)$$
- **Naive Baseline Policy Comparisons**:
  - **Flag Nothing Policy ($\tau = 1.0$) Cost**: ₹3,433,500 $\rightarrow$ **Cost-Optimal Model Saves ₹954,000 (~₹9.54 Lakhs)**.
  - **Flag Everything Policy ($\tau = 0.0$) Cost**: ₹8,800,000 $\rightarrow$ **Cost-Optimal Model Saves ₹6,320,500 (~₹63.2 Lakhs)**.
- **Financial Proof**: Compares total ₹ loss at the **Cost-Optimal Threshold ($\tau = 0.75$)** versus standard F1-optimal threshold, showing exact rupee savings for finance teams.

---

##  Strictly Defense-Only Architecture

- **100% Defensive Risk Mitigation**: Operates purely as a risk assessment, fraud screening, and operational audit console (`"Auto-approve"` vs `"Hold for manual review"`).
- **Zero Offensive Capabilities**: Contains **no offensive code, network probing, or automated counter-maneuvers**. Anything offense-capable is strictly excluded.
- **Audit-Ready Explainability**: Computes single-instance **SHAP factor attributions** for every decision, producing transparent regulatory audit records for RBI / compliance checks.

---

##  Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm
- OpenMP library (`brew install libomp` on macOS)

### 1. Run ML Pipeline & Artifact Generation
```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/labeling.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/features.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/train.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/drift_baseline.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/cost_model.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/cost_sensitivity.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib python3 ml/src/evaluate.py
```

### 2. Start FastAPI Backend Server
```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib PYTHONPATH=. uvicorn backend.app.main:app --port 8000 --reload
```

### 3. Start React Frontend Server
```bash
cd frontend
npm run dev
```
*App URL:* `http://localhost:5173` | *API Docs:* `http://localhost:8000/docs`
