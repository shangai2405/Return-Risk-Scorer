import React, { useState, useEffect } from 'react';
import { fetchExplain } from '../api/client';
import DecisionCard from '../components/DecisionCard';
import ShapBar from '../components/ShapBar';
import { ArrowLeft, FileText, Clock } from 'lucide-react';

export default function OrderDetail({ orderId, onBack }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!orderId) return;
    setLoading(true); setError(null);
    fetchExplain(orderId)
      .then(setDetail)
      .catch(e => setError(e.message || 'Could not load order details'))
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-16 text-center">
      <p className="text-sm text-slate-400">Loading audit trace for order <span className="font-mono">{orderId}</span>...</p>
    </div>
  );

  if (error || !detail) return (
    <div className="bg-white border border-red-200 rounded-xl shadow-sm p-10 text-center">
      <p className="text-red-500 text-sm mb-4">{error || 'Order not found'}</p>
      <button onClick={onBack}
        className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-50 transition">
        Return to Queue
      </button>
    </div>
  );

  return (
    <div className="space-y-5">
      {/* Breadcrumb / Back */}
      <div className="flex items-center justify-between">
        <button onClick={onBack}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition">
          <ArrowLeft className="w-4 h-4" /> Back to Review Queue
        </button>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Clock className="w-3.5 h-3.5" />
          {detail.scored_at ? new Date(detail.scored_at).toLocaleString() : '—'}
        </div>
      </div>

      {/* Header card */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="h-1" style={{ backgroundColor: '#0f2d5c' }} />
        <div className="px-6 py-5 border-b border-slate-100 flex items-start gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-slate-100 border border-slate-200 mt-0.5">
            <FileText className="w-4 h-4" style={{ color: '#0f2d5c' }} />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Order Audit Trace</div>
            <h1 className="text-lg font-bold text-slate-800 mt-0.5">
              Order <span className="font-mono" style={{ color: '#0f2d5c' }}>{detail.order_id}</span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Regulatory-grade SHAP factor attribution and decision record
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 p-6">
          <DecisionCard
            riskScore={detail.risk_score}
            flag={detail.flag}
            threshold={0.67}
            recommendedAction={detail.recommended_action}
          />
          <ShapBar factorDetails={detail.factor_details} />
        </div>
      </div>
    </div>
  );
}
