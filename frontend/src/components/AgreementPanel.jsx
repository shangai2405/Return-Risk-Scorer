import React, { useState, useEffect } from 'react';
import { fetchAgreementStats } from '../api/client';
import { InfoTooltip } from './InfoTooltip';
import { Users, CheckCircle2, AlertOctagon, RefreshCw } from 'lucide-react';

export default function AgreementPanel() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStats = async () => {
    setLoading(true); setError(null);
    try {
      const data = await fetchAgreementStats();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Could not load analyst agreement stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadStats(); }, []);

  if (loading) return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm mb-6 flex items-center justify-between">
      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
        <RefreshCw className="w-4 h-4 animate-spin text-blue-700" />
        Loading analyst feedback & agreement tracking stats...
      </div>
    </div>
  );

  if (error || !stats) return null;

  const isHighTrust = stats.status === 'STABLE_HIGH_TRUST';
  const pct = (stats.agreement_rate * 100).toFixed(1);
  const overturnPct = (stats.overturn_rate * 100).toFixed(1);
  const b = stats.breakdown || {};

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm mb-6 relative">
      <div className={`h-1.5 w-full rounded-t-xl ${isHighTrust ? 'bg-emerald-500' : 'bg-amber-500'}`} />

      <div className="p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-700 shrink-0">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Analyst Agreement & Operational Trust Monitor
                </h3>
                <InfoTooltip text="Tracks human risk analyst agreement vs overturn decisions on scored orders. Signals whether risk ops teams trust model decisions over time." align="right" />
              </div>
              <p className="text-[11px] text-slate-400">
                Total Reviewed Orders: {stats.total_reviewed} &nbsp;·&nbsp; Operational Review Loop
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isHighTrust ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                High Analyst Trust ({pct}%)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
                <AlertOctagon className="w-3.5 h-3.5 text-amber-600" />
                Monitor Declining Trust ({pct}%)
              </span>
            )}
          </div>
        </div>

        {/* 4 Outcome Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-lg">
            <div className="text-[10px] uppercase font-bold text-emerald-800">Confirmed Risk</div>
            <div className="text-lg font-bold text-emerald-900 mt-0.5">{b.confirmed_risk || 0} orders</div>
            <div className="text-[10px] text-emerald-600">Model flagged, Analyst agreed</div>
          </div>
          <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-lg">
            <div className="text-[10px] uppercase font-bold text-emerald-800">Confirmed Safe</div>
            <div className="text-lg font-bold text-emerald-900 mt-0.5">{b.confirmed_safe || 0} orders</div>
            <div className="text-[10px] text-emerald-600">Model approved, Analyst agreed</div>
          </div>
          <div className="p-3 bg-amber-50/50 border border-amber-100 rounded-lg">
            <div className="text-[10px] uppercase font-bold text-amber-800">Overturned Safe</div>
            <div className="text-lg font-bold text-amber-900 mt-0.5">{b.overturned_safe || 0} orders</div>
            <div className="text-[10px] text-amber-700">Model flagged, Analyst cleared</div>
          </div>
          <div className="p-3 bg-amber-50/50 border border-amber-100 rounded-lg">
            <div className="text-[10px] uppercase font-bold text-amber-800">Overturned Risk</div>
            <div className="text-lg font-bold text-amber-900 mt-0.5">{b.overturned_risk || 0} orders</div>
            <div className="text-[10px] text-amber-700">Model approved, Analyst caught</div>
          </div>
        </div>
      </div>
    </div>
  );
}
