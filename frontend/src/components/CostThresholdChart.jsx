import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, ReferenceDot, ReferenceLine, CartesianGrid
} from 'recharts';
import { SlidersHorizontal, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

export default function CostThresholdChart({ metrics }) {
  if (!metrics || !metrics.cost_curve) return null;

  const costCurve = metrics.cost_curve;
  const [threshold, setThreshold] = useState(metrics.chosen_threshold || 0.67);

  const currentPoint = useMemo(() => {
    return costCurve.reduce((prev, curr) =>
      Math.abs(curr.threshold - threshold) < Math.abs(prev.threshold - threshold) ? curr : prev
    , costCurve[0]);
  }, [costCurve, threshold]);

  const minPoint = useMemo(() => {
    return costCurve.reduce((prev, curr) => curr.cost < prev.cost ? curr : prev, costCurve[0]);
  }, [costCurve]);

  const isOptimal = Math.abs(threshold - minPoint.threshold) < 0.005;

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm mb-6 relative">
      {/* Panel Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4" style={{ color: '#0f2d5c' }} />
            Cost-Based Threshold Optimizer
            <InfoTooltip text="Adjust the probability cutoff to balance False Alarm costs (FP @ ₹500) against Missed Return costs (FN @ ₹1,500). The curve shows total business loss at each threshold." />
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            False Alarm Cost: ₹500 &nbsp;·&nbsp; Missed Return Cost: ₹1,500
          </p>
        </div>

        {/* Live KPI badges */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="text-center px-4 py-2 rounded-lg border border-slate-200 bg-slate-50 min-w-[100px]">
            <div className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider flex items-center justify-center gap-1">
              Cutoff (τ) <InfoTooltip text="Orders scoring above this probability are flagged for review." />
            </div>
            <div className="text-lg font-bold font-mono mt-0.5" style={{ color: '#0f2d5c' }}>
              {currentPoint.threshold.toFixed(2)}
            </div>
          </div>
          <div className="text-center px-4 py-2 rounded-lg border border-amber-200 bg-amber-50 min-w-[120px]">
            <div className="text-[10px] font-semibold uppercase text-amber-600 tracking-wider">
              Simulated Loss
            </div>
            <div className="text-lg font-bold text-amber-700 mt-0.5">
              ₹{currentPoint.cost.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="px-6 pt-4 h-60">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={costCurve} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="threshold"
              stroke="#94a3b8"
              tickFormatter={v => v.toFixed(2)}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
            />
            <YAxis
              stroke="#94a3b8"
              tickFormatter={v => `₹${(v/1000).toFixed(0)}k`}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', borderColor: '#e2e8f0', borderRadius: '8px', color: '#1e293b', fontSize: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
              formatter={value => [`₹${Number(value).toLocaleString()}`, 'Total Cost']}
              labelFormatter={label => `Threshold: ${Number(label).toFixed(2)}`}
            />
            <Line type="monotone" dataKey="cost" stroke="#0f2d5c" strokeWidth={2.5} dot={false} activeDot={{ r: 5, fill: '#0f2d5c' }} />
            <ReferenceDot x={minPoint.threshold} y={minPoint.cost} r={6} fill="#10b981" stroke="#fff" strokeWidth={2} />
            <ReferenceLine x={currentPoint.threshold} stroke="#f59e0b" strokeDasharray="4 3" strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Slider & info */}
      <div className="px-6 pb-4 pt-3">
        <div className="flex justify-between text-[11px] text-slate-400 font-medium mb-1.5">
          <span>0.05 — Strict Review</span>
          <span className="font-semibold text-slate-600">τ = {threshold.toFixed(2)}</span>
          <span>0.95 — Permissive</span>
        </div>
        <input
          type="range" min="0.05" max="0.95" step="0.01" value={threshold}
          onChange={e => setThreshold(parseFloat(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-[11px] text-slate-400 mt-2">
          <span>
            False Alarms: <span className="font-semibold text-slate-600">{currentPoint.fp}</span> orders
            &nbsp;(₹{(currentPoint.fp * 500).toLocaleString()})
          </span>
          <span>
            Missed Returns: <span className="font-semibold text-slate-600">{currentPoint.fn}</span> orders
            &nbsp;(₹{(currentPoint.fn * 1500).toLocaleString()})
          </span>
        </div>

        <div className={`mt-3 px-4 py-2.5 rounded-lg border text-xs font-medium flex items-center justify-between
          ${isOptimal
            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
            : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
          <span className="flex items-center gap-1.5">
            {isOptimal
              ? <><CheckCircle2 className="w-3.5 h-3.5" />Currently at optimal threshold — minimum business loss achieved</>
              : <><AlertTriangle className="w-3.5 h-3.5" />Optimal threshold is τ = {minPoint.threshold} (Loss: ₹{minPoint.cost.toLocaleString()})</>
            }
          </span>
          {!isOptimal && (
            <button
              onClick={() => setThreshold(minPoint.threshold)}
              className="ml-4 font-semibold underline underline-offset-2 text-amber-800 hover:text-amber-900"
            >
              Reset to τ = {minPoint.threshold}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
