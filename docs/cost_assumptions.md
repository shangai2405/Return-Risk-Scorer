# Cost-Based Thresholding & Business Assumptions (Indian BFSI & E-Commerce Context)

## 1. Indian BFSI & Fintech Business Cost Constants

The Return-Risk Scorer optimizes decision thresholds based on explicit financial cost metrics in Indian Rupee (₹), tailored for Indian BFSI, Payment Gateways (e.g. Razorpay, Cashfree, Paytm), and E-Commerce Merchants.

- **False Positive Cost ($C_{\text{FP}}$)**: **₹500**
  - *Definition*: Flagging a low-risk order for manual review when the customer would not have initiated a return/dispute.
  - *Cost Drivers*: Risk Operations team manual review labor, customer dispatch delay, support ticket friction (~₹500 flat administrative overhead).

- **False Negative Cost ($C_{\text{FN}}$)**: **₹1,500**
  - *Definition*: Auto-approving a high-risk order that subsequently gets returned, disputed, or results in Return-To-Origin (RTO) loss.
  - *Cost Drivers*: Reverse logistics shipping costs (RTO charges), item restocking/damage loss, payment gateway dispute fee, support processing (~₹1,500 flat financial loss).

---

## 2. Total Business Loss Formulation

For any classification probability threshold $\tau \in [0, 1]$, the total business loss $L(\tau)$ on a validation/test dataset is defined as:

$$L(\tau) = \text{FP}(\tau) \times 500 + \text{FN}(\tau) \times 1500$$

Where:
- $\text{FP}(\tau)$ is the number of low-risk orders flagged as high-risk at threshold $\tau$.
- $\text{FN}(\tau)$ is the number of high-risk orders auto-approved at threshold $\tau$.

---

## 3. Threshold Selection Objective & Honest Metrics

Instead of selecting a threshold $\tau$ that maximizes F1-score (which treats FP and FN as equally weighted errors), our system sweeps thresholds $\tau \in [0.05, 0.95]$ in increments of $0.01$ and selects:

$$\tau^* = \arg\min_{\tau} L(\tau)$$

### Naive Baseline Policy Comparison:
To evaluate true financial impact, we compare our Cost-Optimal Threshold against two extreme operational baseline policies on the 19,889 test set transactions:

1. **Flag Nothing Policy ($\tau = 1.0$)**: Auto-approves all orders without screening. Total Loss = ₹3,433,500.
2. **Flag Everything Policy ($\tau = 0.0$)**: Flags all orders for manual review. Total Loss = ₹8,800,000.
3. **Cost-Optimal Model ($\tau = 0.75$)**: Total Loss = **₹2,479,500**.
   - **Net Financial Savings vs. Flag Nothing**: **₹954,000** (~₹9.54 Lakhs saved on 19.8k orders).
   - **Net Financial Savings vs. Flag Everything**: **₹6,320,500** (~₹63.2 Lakhs saved on 19.8k orders).

### Sensitivity of Threshold Selection (Cost-Ratio Sweep):
To test the robustness of our ₹500 / ₹1,500 cost assumption, `ml/src/cost_sensitivity.py` fixes $C_{\text{FP}} = ₹500$ and sweeps $C_{\text{FN}}$ from ₹500 to ₹5,000 (ratio 1:1 to 1:10). The resulting optimal threshold shifts smoothly across ratios, proving that the decision boundary responds predictably to cost assumptions rather than exhibiting fragile behavior.

---

## 4. Defense-Only Compliance Statement

- **100% Defensive Risk Mitigation**: The system acts strictly as an internal risk scoring, fraud screening, and operational review tool.
- **Zero Offensive Capabilities**: The system executes no counter-attacks, external network probes, or offensive maneuvers. It evaluates internal transaction vectors to output defense recommendations (`"Auto-approve"` vs `"Hold for manual review"`).
