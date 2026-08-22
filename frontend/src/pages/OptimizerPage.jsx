import React from 'react';
import CostThresholdChart from '../components/CostThresholdChart';
import CostSensitivityChart from '../components/CostSensitivityChart';

export default function OptimizerPage({ metrics }) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Risk Tuning</span>
          <h1 className="text-xl font-bold text-slate-800 mt-0.5">Financial Threshold Optimizer</h1>
          <p className="text-xs text-slate-500 mt-1">
            Adjust the risk cutoff probability threshold to achieve minimum business financial loss
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs bg-slate-50 border border-slate-200 rounded-lg p-3">
          <div>
            <div className="text-slate-400 font-medium">False Alarm Cost</div>
            <div className="font-bold text-slate-700">₹500 / order</div>
          </div>
          <div className="h-6 w-px bg-slate-200" />
          <div>
            <div className="text-slate-400 font-medium">Missed Return Cost</div>
            <div className="font-bold text-slate-700">₹1,500 / order</div>
          </div>
        </div>
      </div>

      <CostThresholdChart metrics={metrics} />

      <CostSensitivityChart sensitivityData={metrics?.cost_sensitivity} />
    </div>
  );
}
