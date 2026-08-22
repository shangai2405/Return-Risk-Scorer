# Return-Risk Labeling Methodology & Empirical Thresholding

## 1. Ground Truth Proxy Label Definition

In e-commerce and transaction risk management, explicit post-delivery return transactions require objective proxy modeling. An order is flagged as **High Return Risk** (`return_risk \in \{0, 1\}`) if any of the following three business conditions are met:

1. **Review Score Dissatisfaction**: `review_score <= 2`
2. **Empirical Delivery Delay**: `delivery_delay_days > 4` (derived from dataset 90th percentile delay)
3. **Repeat Low-Review Customer**: `prior_low_review_count >= 2` (derived from repeat customer low-review distribution)

---

## 2. Empirical Percentile-Based Threshold Derivation

Rather than assuming arbitrary fixed guesses (such as a generic "7 days" or "3 complaints"), our labeling pipeline computes the empirical distributions directly from `ml/data/raw/` prior to applying the rule and saves the exact config to `ml/artifacts/labeling_thresholds.json`:

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

### Empirical Results Summary:
- **Delivery Delay Threshold**: The 90th percentile delivery delay across all orders was evaluated at **4 days** (relative to estimated delivery date). Therefore, `delivery_delay_days > 4` is set as the operational delay threshold, ensuring the cutoff reflects extreme logistics friction rather than minor carrier variance.
- **Prior Low-Review Threshold**: Among repeat customers ($\ge 1$ prior order), $2,818$ customers had $0$ low reviews, $507$ had $1$, $19$ had $2$, and $1$ had $3$. The threshold $\ge 2$ represents the smallest integer value where fewer than $10\%$ ($<1.0\%$) of repeat customers exceed it.
- **Review Score Threshold**: `review_score <= 2` is maintained with explicit semantic justification: Olist's own 5-star rating scale treats 1 and 2 stars as explicit buyer dissatisfaction and complaint triggers.

### Why Percentile-Based Thresholding is Defensible:
Percentile-based thresholding is significantly more defensible than hardcoded guesses because it adapts dynamically to the target market's actual operational environment. E-commerce logistics and buyer behavior vary dramatically across regions (e.g. Brazilian logistics vs. domestic Indian express dispatch). By deriving thresholds from empirical percentiles (90th percentile delay cutoff and top 10% repeat complaint tail), the labeling logic reflects true statistical anomalies within this specific dataset rather than imposing arbitrary assumptions that might misclassify standard fulfillment performance in a different market.

---

## 3. Strict Data Leakage Safeguards

- **Chronological Expanding Counts**: `prior_low_review_count` and `customer_order_count` are computed strictly using past orders preceding the current order's `order_purchase_timestamp`.
- **Temporal Split**: Model training and evaluation use a strict 80% train / 20% test chronological time split.
- **Single Source of Truth**: `labeling.py` computes and writes `labeling_thresholds.json`, then reads these exact parameters back in when constructing `labeled_orders.csv`.

---

## 4. Defense-Only Architecture

This platform operates strictly as an internal **Defensive Risk Management & Audit Engine**:
- **Audit-Ready SHAP Attributions**: Explains every decision for regulatory and compliance review.
- **Zero Offensive Actions**: Contains zero offensive or automated counter-blocking mechanisms.
