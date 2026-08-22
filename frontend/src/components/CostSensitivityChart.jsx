import React from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, ReferenceDot, CartesianGrid
} from 'recharts';
import { ShieldAlert, Info } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

export default function CostSensitivityChart({ sensitivityData }) {
  if (!sensitivityData || !sensitivityData.sweep) return null;

  const sweep = sensitivityData.sweep;
  const chosenRatio = sensitivityData.chosen_ratio || '1:3';
  const chosenPoint = sweep.find(s => s.ratio === chosenRatio) || sweep[4];
  const stabilityNote = sensitivityData.stability_note || 'Threshold choice evaluated across cost ratios.';

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm mb-6 overflow-hidden">
      {/* Panel Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-blue-700" />
            Cost-Ratio Sensitivity Analysis (FP:FN Ratio Sweep)
            <InfoTooltip text="Evaluates how the optimal decision threshold shifts across different False Positive to False Negative cost ratios (1:1 up to 1:10). Proves decision stability across varying cost estimates." align="right" />
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Fixed FP = ₹500 &nbsp;·&nbsp; Swept FN = ₹500 to ₹5,000 &nbsp;·&nbsp; Chosen Anchor = 1:3 (₹500 / ₹1,500)
          </p>
        </div>

        {/* Anchor badge */}
        <div className="text-center px-4 py-2 rounded-lg border border-blue-200 bg-blue-50/60 shrink-0">
          <div className="text-[10px] font-semibold uppercase text-blue-800 tracking-wider">
            Anchor Cutoff (1:3)
          </div>
          <div className="text-base font-bold text-blue-900 font-mono mt-0.5">
            τ = {chosenPoint.optimal_threshold}
          </div>
        </div>
      </div>

      {/* Line Chart */}
      <div className="px-6 pt-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={sweep} margin={{ top: 5, right: 15, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="ratio"
              stroke="#94a3b8"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
            />
            <YAxis
              stroke="#94a3b8"
              domain={[0.0, 1.0]}
              tickFormatter={v => v.toFixed(2)}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', borderColor: '#e2e8f0', borderRadius: '8px', color: '#1e293b', fontSize: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
              formatter={(value, name) => [value, name === 'optimal_threshold' ? 'Optimal Threshold (τ)' : 'Total Cost']}
              labelFormatter={label => `Cost Ratio (FP:FN): ${label}`}
            />
            <Line type="monotone" dataKey="optimal_threshold" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} />
            {chosenPoint && (
              <ReferenceDot x={chosenPoint.ratio} y={chosenPoint.optimal_threshold} r={7} fill="#0f2d5c" stroke="#fff" strokeWidth={2} />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Stability Note */}
      <div className="px-6 pb-4 pt-2">
        <div className="flex items-start gap-2 px-4 py-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-700">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <span>{stabilityNote}</span>
        </div>
      </div>
    </div>
  );
}
