# Statistical Data Drift Monitoring Specification

## 1. Overview & Business Rationale

Machine learning models deployed in financial risk environments face **covariate shift and data drift** over time. A return-risk model trained on historical 2017–2018 e-commerce fulfillment data may silently suffer precision/recall degradation if production shipping patterns, buyer payment habits, or installment trends shift.

To prevent silent model degradation in production, the Return-Risk Scorer incorporates a **pure statistical Data Drift Monitoring Module** that operates out-of-band as an executive risk control.

> [!IMPORTANT]
> **Strictly Side-Effect Free**: The Drift Monitoring Module is a read-only, diagnostic risk control. It **never modifies model weights, predictions, scoring probabilities, or threshold cutoffs**.

---

## 2. Statistical Drift Metrics & Thresholds

### A. Two-Sample Kolmogorov-Smirnov (KS) Test (Numeric Features)
For continuous numeric features (e.g., `delivery_delay_days`, `order_value`, `freight_value`, `customer_order_count`, `prior_low_review_count`, `installments`):

- **Method**: `scipy.stats.ks_2samp` compares the empirical cumulative distribution function (eCDF) of a rolling window of production transactions ($N = 200$) against the baseline training distribution snapshot ($N = 1000$).
- **Statistical Significance Threshold**:
  $$\text{Drift Detected if } p\text{-value} < 0.05$$
  A $p$-value $< 0.05$ indicates statistically significant evidence at the 95% confidence level that the production distribution no longer matches the training baseline.

### B. Population Stability Index (PSI) (Categorical & One-Hot Features)
For categorical and one-hot encoded features (e.g., `payment_type_boleto`, `address_state_mismatch`, top product categories):

- **Method**: Computes Population Stability Index comparing production rolling window proportions ($A_i$) against baseline expected proportions ($E_i$):
  $$\text{PSI} = \sum_{i} \left( A_i - E_i \right) \times \ln\left(\frac{A_i}{E_i}\right)$$
- **Industry Standard Shift Threshold**:
  - $\text{PSI} < 0.1$: Stable (no significant shift).
  - $0.1 \le \text{PSI} \le 0.2$: Moderate shift (monitor closely).
  - **$\text{PSI} > 0.2$**: **Drift Detected** (significant structural population shift).

---

## 3. Production Architecture & Performance Isolation

1. **Baseline Snapshot (`ml/artifacts/drift_baseline.json`)**: Generated on the training set snapshot after model training. Stores 10-bin histograms, category proportions, and raw sample caches for fast KS evaluation.
2. **Rolling Window Logging (`production_features` SQLite Table)**: Wide-format table storing input vectors of scored orders.
3. **On-Demand Execution (`GET /drift-status`)**: Computed asynchronously on-demand rather than inline on every request, ensuring zero latency impact on the real-time scoring path.
4. **Static Template Explanations**: Mapped plain-language alerts (keyed by feature name) informing risk managers of exact operational shifts (e.g., *"Delivery delays trending significantly higher than training data — model may be under-flagging risk"*).
