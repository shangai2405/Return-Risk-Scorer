import React from 'react';
import { Target, Activity, Award, ShieldCheck, DollarSign } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

function StatCard({ label, value, sub, icon: Icon, iconColor, tooltip, highlight, align }) {
  return (
    <div className={`bg-white rounded-xl p-5 shadow-sm border flex flex-col gap-1 ${highlight ? 'border-blue-200' : 'border-slate-200'}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center">
          {label}
          {tooltip && <InfoTooltip text={tooltip} align={align} />}
        </span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-slate-50 border border-slate-100">
          <Icon className="w-4 h-4" style={{ color: iconColor || '#0f2d5c' }} />
        </div>
      </div>
      <div className={`text-3xl font-bold tracking-tight ${highlight ? '' : 'text-slate-800'}`}
           style={highlight ? { color: '#0f2d5c' } : {}}>
        {value}
      </div>
      <div className="text-xs text-slate-400 font-medium">{sub}</div>
    </div>
  );
}

export default function MetricCards({ metrics }) {
  if (!metrics) return null;
  const costOpt = metrics.eval_results?.cost_optimal || {};

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <StatCard
        label="Precision"
        value={`${(costOpt.precision * 100 || 0).toFixed(1)}%`}
        sub="Flag accuracy rate"
        icon={Target}
        iconColor="#10b981"
        tooltip="Out of all orders flagged as High Risk, this percentage were actually risky."
      />
      <StatCard
        label="Recall"
        value={`${(costOpt.recall * 100 || 0).toFixed(1)}%`}
        sub="Returns detected"
        icon={Activity}
        iconColor="#3b82f6"
        tooltip="Out of all actual bad orders, this percentage was caught by the system."
      />
      <StatCard
        label="F1 Score"
        value={`${(costOpt.f1 * 100 || 0).toFixed(1)}%`}
        sub="Balanced accuracy"
        icon={Award}
        iconColor="#8b5cf6"
        tooltip="A combined accuracy score balancing Precision and Recall together."
      />
      <StatCard
        label="ROC-AUC"
        value={(metrics.roc_auc || 0).toFixed(3)}
        sub="Model intelligence"
        icon={ShieldCheck}
        iconColor="#0ea5e9"
        tooltip="Measures AI's ability to distinguish safe vs risky orders (0.5 = random, 1.0 = perfect)."
        align="right"
      />
      <StatCard
        label="Min Business Loss"
        value={`₹${(metrics.total_cost_at_threshold || 0).toLocaleString()}`}
        sub={`Threshold τ = ${metrics.chosen_threshold}`}
        icon={DollarSign}
        iconColor="#f59e0b"
        tooltip="Lowest total financial loss when risk cutoff is at the optimal probability threshold."
        highlight
        align="right"
      />
    </div>
  );
}
