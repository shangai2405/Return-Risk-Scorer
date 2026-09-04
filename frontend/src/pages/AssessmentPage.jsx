import React, { useState } from 'react';
import DecisionCard from '../components/DecisionCard';
import ShapBar from '../components/ShapBar';
import { InfoTooltip } from '../components/InfoTooltip';
import { scoreOrder } from '../api/client';
import { Play, AlertCircle, ShieldAlert, ShieldCheck, ChevronDown, Activity } from 'lucide-react';

// delivery_delay_days — accepted by backend schema but silently dropped before scoring
// (feature is not in the model's feature_cols; retained in payload for schema stability).
// prior_low_review_count — removed from model features to fix label/feature circularity
// (it was one of three conditions defining return_risk=1; including it as a raw input
// let the model trivially recover the labeling rule rather than learning genuine signal).
// Both fields are sent in the API payload with fixed defaults but are NOT exposed in the
// UI — showing editable fields whose values don't move the score is a live demo failure.
const FIELD_META = {
  order_value:  { label: 'Order Value (₹)',    tip: 'Total price of all items in the customer cart.',                    required: true },
  freight_value: { label: 'Freight Fee (₹)',   tip: 'Shipping and logistics fee billed for this fulfillment.',           required: true },
  installments: { label: 'Installment Months', tip: 'Number of monthly installments selected by the customer.',          required: true },
};

export default function AssessmentPage() {
  const [inputs, setInputs] = useState({
    order_id: 'ORD-SANDBOX-01',
    order_value: '280',
    freight_value: '35',
    installments: '3',
    discount_flag: 0,
    customer_order_count: '1',
    address_state_mismatch: 1,
    payment_type: 'boleto',
    product_category: 'health_beauty',
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validError, setValidError] = useState(null);
  const [apiError, setApiError] = useState(null);

  const set = (field, val) => { setInputs(p => ({ ...p, [field]: val })); setValidError(null); };

  const fillHigh = () => {
    setInputs({ order_id: 'ORD-HIGH-01', order_value: '450', freight_value: '65',
      installments: '6', discount_flag: 0,
      customer_order_count: '1',
      address_state_mismatch: 1, payment_type: 'boleto', product_category: 'health_beauty' });
    setValidError(null); setResult(null);
  };

  const fillLow = () => {
    setInputs({ order_id: 'ORD-SAFE-01', order_value: '120', freight_value: '15',
      installments: '1', discount_flag: 0,
      customer_order_count: '1',
      address_state_mismatch: 0, payment_type: 'credit_card', product_category: 'health_beauty' });
    setValidError(null); setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidError(null); setApiError(null);

    // Validate required fields — no blanks allowed
    for (const [key, meta] of Object.entries(FIELD_META)) {
      if (meta.required && String(inputs[key] ?? '').trim() === '') {
        setValidError(`"${meta.label}" cannot be blank. Please enter a valid value before submitting.`);
        return;
      }
    }

    setLoading(true);
    try {
      const payload = {
        order_id: inputs.order_id || 'ORD-DYNAMIC',
        order_value: parseFloat(inputs.order_value),
        freight_value: parseFloat(inputs.freight_value),
        installments: parseInt(inputs.installments, 10),
        // delivery_delay_days: sent as default 0.0 — field is accepted by API schema
        // but dropped before inference (not in model feature_cols).
        delivery_delay_days: 0.0,
        discount_flag: inputs.discount_flag,
        customer_order_count: parseInt(inputs.customer_order_count, 10) || 0,
        // prior_low_review_count: sent as 0 — removed from model features to fix
        // label/feature circularity. Kept in payload for backend schema stability.
        prior_low_review_count: 0,
        address_state_mismatch: inputs.address_state_mismatch,
        payment_type: inputs.payment_type,
        product_category: inputs.product_category,
      };
      const res = await scoreOrder(payload);
      setResult(res);
    } catch (err) {
      setApiError(err.message || 'Scoring service unavailable');
    } finally {
      setLoading(false);
    }
  };

  const inputCls = "w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-800 bg-white placeholder-slate-300 focus:outline-none focus:border-blue-500 transition font-medium";

  return (
    <div className="space-y-6">
      {/* Assessment Form Panel */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {/* Navy header bar */}
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
             style={{ borderTop: '4px solid #0f2d5c' }}>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-0.5">
              Enterprise Risk Module
            </div>
            <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <Activity className="w-5 h-5" style={{ color: '#0f2d5c' }} />
              Live Order Risk Assessment Console
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Submit order parameters to receive instant AI return risk probability and SHAP explainability audit breakdown
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button type="button" onClick={fillHigh}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-red-200 bg-red-50 text-red-600 hover:bg-red-100 transition">
              <ShieldAlert className="w-3.5 h-3.5" /> High-Risk Sample
            </button>
            <button type="button" onClick={fillLow}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-emerald-200 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 transition">
              <ShieldCheck className="w-3.5 h-3.5" /> Low-Risk Sample
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-5 gap-y-4 mb-5">

            {/* Numeric required fields */}
            {Object.entries(FIELD_META).map(([key, meta]) => (
              <div key={key}>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                  {meta.label} <span className="text-red-500">*</span>
                  <InfoTooltip text={meta.tip} />
                </label>
                <input
                  type="number"
                  step="any"
                  value={inputs[key]}
                  placeholder="—"
                  onChange={e => set(key, e.target.value)}
                  className={inputCls}
                />
              </div>
            ))}

            {/* Payment Instrument */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Payment Instrument
                <InfoTooltip text="Method used for checkout. Boleto and vouchers carry elevated return risk." />
              </label>
              <div className="relative">
                <select
                  value={inputs.payment_type}
                  onChange={e => set('payment_type', e.target.value)}
                  className={inputCls + ' appearance-none pr-8'}
                >
                  <option value="credit_card">Credit Card</option>
                  <option value="boleto">Boleto Cash Voucher</option>
                  <option value="voucher">Store Voucher</option>
                  <option value="debit_card">Debit Card</option>
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
              </div>
            </div>

            {/* State Mismatch */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                State Location
                <InfoTooltip text="Whether buyer and seller are in different states — higher cross-state distance correlates with delayed/failed delivery." />
              </label>
              <div className="relative">
                <select
                  value={inputs.address_state_mismatch}
                  onChange={e => set('address_state_mismatch', parseInt(e.target.value, 10))}
                  className={inputCls + ' appearance-none pr-8'}
                >
                  <option value={0}>Same State</option>
                  <option value={1}>Cross-State Mismatch</option>
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
              </div>
            </div>

            {/* Submit button aligned to field grid */}
            <div className="flex items-end lg:col-span-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-sm font-bold text-white transition hover:opacity-90 disabled:opacity-60 shadow-sm"
                style={{ backgroundColor: '#0f2d5c' }}
              >
                <Play className="w-4 h-4 fill-current" />
                {loading ? 'Processing...' : 'Run Risk Assessment'}
              </button>
            </div>
          </div>

          {/* Validation error */}
          {validError && (
            <div className="flex items-start gap-2 px-4 py-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-xs font-medium mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-amber-500" />
              {validError}
            </div>
          )}

          {/* API error */}
          {apiError && (
            <div className="flex items-start gap-2 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-xs font-medium mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              {apiError}
            </div>
          )}
        </form>

        {/* Result area */}
        {result && (
          <div className="border-t border-slate-100 px-6 py-5">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
              Assessment Result — Order <span className="font-mono text-slate-600">{result.order_id}</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <DecisionCard
                riskScore={result.risk_score}
                flag={result.flag}
                threshold={result.threshold}
                recommendedAction={result.recommended_action}
              />
              <ShapBar factorDetails={result.factor_details} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
