import React from 'react';
import { AlertOctagon, CheckCircle2 } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

export default function DecisionCard({ riskScore, flag, threshold, recommendedAction }) {
  const pct = (riskScore * 100).toFixed(1);

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm relative">
      {/* Status bar at top */}
      <div className={`h-1.5 w-full ${flag ? 'bg-red-500' : 'bg-emerald-500'}`} />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1">
            Decision Assessment
            <InfoTooltip text="The AI model's risk verdict for this transaction, based on the configured probability threshold." />
          </h3>
          {flag ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-600 border border-red-200">
              <AlertOctagon className="w-3.5 h-3.5" /> High Risk
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-600 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" /> Cleared
            </span>
          )}
        </div>

        {/* Score display */}
        <div className="flex items-end justify-between mb-3">
          <div>
            <div className="text-xs text-slate-400 font-medium flex items-center">
              Return Risk Probability
              <InfoTooltip text="The model's estimated probability (0–100%) that this order will result in a return or complaint." />
            </div>
            <div className={`text-5xl font-black tracking-tight mt-1 ${flag ? 'text-red-500' : 'text-emerald-600'}`}>
              {pct}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-slate-400 uppercase font-semibold flex items-center justify-end">
              Decision Cutoff
              <InfoTooltip text="Orders above this probability threshold are flagged for review." />
            </div>
            <div className="text-sm font-bold font-mono mt-1" style={{ color: '#0f2d5c' }}>
              τ = {threshold?.toFixed(2) || '0.67'}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-slate-100 rounded-full h-2 mb-4 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${flag ? 'bg-red-500' : 'bg-emerald-500'}`}
            style={{ width: `${Math.min(100, riskScore * 100)}%` }}
          />
        </div>

        {/* Recommended Action */}
        <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-4 py-3">
          <span className="text-xs font-semibold text-slate-500 flex items-center">
            Recommended Action
            <InfoTooltip text="'Hold for manual review' blocks auto-dispatch. 'Auto-approve' sends order directly to fulfillment." />
          </span>
          <span className={`text-sm font-bold ${flag ? 'text-red-600' : 'text-emerald-600'}`}>
            {recommendedAction}
          </span>
        </div>
      </div>
    </div>
  );
}
