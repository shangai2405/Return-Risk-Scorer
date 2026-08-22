import React, { useState, useEffect } from 'react';
import { fetchOrders, submitReview } from '../api/client';
import { ShieldAlert, ChevronRight, Search, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';

export default function ReviewQueue({ onSelectOrder }) {
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviewedDict, setReviewedDict] = useState({});

  const load = async () => {
    setLoading(true); setError(null);
    try { setOrders(await fetchOrders(filter)); }
    catch (e) { setError(e.message || 'Failed to load orders'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleReviewAction = async (e, orderId, decision) => {
    e.stopPropagation();
    try {
      await submitReview(orderId, decision);
      setReviewedDict(prev => ({ ...prev, [orderId]: decision }));
    } catch (err) {
      alert('Error submitting review: ' + err.message);
    }
  };

  const filtered = orders.filter(o => o.order_id.toLowerCase().includes(search.toLowerCase()));

  const FILTERS = [
    { key: 'high_risk', label: 'High Risk' },
    { key: 'low_risk',  label: 'Auto-Approved' },
    { key: null,        label: 'All Orders' },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      {/* Navy top accent */}
      <div className="h-1" style={{ backgroundColor: '#0f2d5c' }} />

      {/* Panel Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" style={{ color: '#0f2d5c' }} />
            Audit Review Queue & Analyst Feedback
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Orders scored by risk engine — click row to view SHAP breakdown or submit analyst review decision
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search order ID..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-500 bg-white"
            />
          </div>

          {/* Filter tabs */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
            {FILTERS.map(f => (
              <button key={String(f.key)} onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 rounded-md font-semibold transition ${
                  filter === f.key ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}>
                {f.label}
              </button>
            ))}
          </div>

          <button onClick={load}
            className="p-2 border border-slate-200 rounded-lg bg-white hover:bg-slate-50 text-slate-500 transition">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-16 text-slate-400 text-sm">Loading orders...</div>
      ) : error ? (
        <div className="text-center py-16 text-red-400 text-sm">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-slate-400 text-sm">No orders found.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                <th className="text-left px-6 py-3">Order ID</th>
                <th className="text-left px-4 py-3">Risk Score</th>
                <th className="text-left px-4 py-3">Primary Risk Factor</th>
                <th className="text-left px-4 py-3">Decision</th>
                <th className="text-left px-4 py-3">Analyst Action</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map(ord => {
                const reviewedAction = reviewedDict[ord.order_id];
                return (
                  <tr key={ord.id}
                    onClick={() => onSelectOrder(ord.order_id)}
                    className="hover:bg-slate-50 cursor-pointer transition group">
                    <td className="px-6 py-3.5 font-mono text-sm text-slate-700 font-medium">{ord.order_id}</td>
                    <td className="px-4 py-3.5">
                      <span className={`text-sm font-bold font-mono ${ord.flag ? 'text-red-500' : 'text-emerald-600'}`}>
                        {(ord.risk_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-500 max-w-xs truncate">
                      {ord.top_factors?.[0] || '—'}
                    </td>
                    <td className="px-4 py-3.5">
                      {ord.flag ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-50 text-red-600 border border-red-200">
                          Hold for Review
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-600 border border-emerald-200">
                          Auto-Approved
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      {reviewedAction ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Reviewed: {reviewedAction.replace('_', ' ')}
                        </span>
                      ) : ord.flag ? (
                        <div className="flex items-center gap-1.5" onClick={e => e.stopPropagation()}>
                          <button
                            onClick={e => handleReviewAction(e, ord.order_id, 'confirmed_risk')}
                            className="px-2 py-1 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded text-[10px] font-bold transition"
                          >
                            Confirm Risk
                          </button>
                          <button
                            onClick={e => handleReviewAction(e, ord.order_id, 'overturned_safe')}
                            className="px-2 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded text-[10px] font-semibold transition"
                          >
                            Overturn (Safe)
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5" onClick={e => e.stopPropagation()}>
                          <button
                            onClick={e => handleReviewAction(e, ord.order_id, 'confirmed_safe')}
                            className="px-2 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded text-[10px] font-semibold transition"
                          >
                            Confirm Safe
                          </button>
                          <button
                            onClick={e => handleReviewAction(e, ord.order_id, 'overturned_risk')}
                            className="px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded text-[10px] font-bold transition"
                          >
                            Overturn (Risk)
                          </button>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
