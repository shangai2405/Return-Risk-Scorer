# Human-Analyst Feedback Loop & Operational Agreement Tracking

## 1. Overview & Operational Rationale

Risk models in production do not operate in a vacuum — they assist human risk operations teams who review flagged transactions and perform spot checks on auto-approved orders.

To monitor operational trust and detect early signals of model degradation before performance metrics decay, the Return-Risk Scorer incorporates a **Human-Analyst Feedback Loop & Agreement Tracking Module**.

---

## 2. Decision Outcomes & Metrics

Analysts review transactions in the **Audit Review Queue** and submit explicit decisions (`POST /orders/{order_id}/review`). The system tracks four distinct operational outcomes:

1. **Confirmed Risk (`confirmed_risk`)**: Model flagged the transaction as high-risk, and the analyst confirmed it was indeed a high-risk transaction.
2. **Confirmed Safe (`confirmed_safe`)**: Model auto-approved the transaction, and the analyst confirmed it was safe.
3. **Overturned Safe (`overturned_safe`)**: Model flagged the transaction as high-risk, but the analyst cleared it as safe (false alarm overturned).
4. **Overturned Risk (`overturned_risk`)**: Model auto-approved the transaction, but the analyst caught a missed risk (false negative caught).

### Derived Key Performance Indicators (KPIs):
- **Agreement Rate**:
  $$\text{Agreement Rate} = \frac{\text{Confirmed Risk} + \text{Confirmed Safe}}{\text{Total Reviewed}}$$
- **Overturn Rate**:
  $$\text{Overturn Rate} = \frac{\text{Overturned Safe} + \text{Overturned Risk}}{\text{Total Reviewed}}$$

---

## 3. Declining Agreement Triggers & Operational Guidance

- **Operational Trust Threshold**:
  - $\text{Agreement Rate} \ge 80\%$: **Stable High Operational Trust** (`STABLE_HIGH_TRUST`).
  - $\text{Agreement Rate} < 80\%$: **Monitor Declining Trust** (`MONITOR_DECLINING_TRUST`).

### What Declining Agreement Signals:
A declining agreement rate is often an **earlier warning signal than statistical data drift**, as human analysts spot emerging fraud patterns or operational policy shifts before feature distributions reflect them. When declining agreement is detected:
1. Review the last $N$ overturned decisions to identify specific feature patterns driving analyst overrides.
2. Consider re-sweeping cost thresholds or triggering a model retraining pipeline.
