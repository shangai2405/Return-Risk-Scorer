import React from 'react';
import MetricCards from '../components/MetricCards';
import DriftPanel from '../components/DriftPanel';
import AgreementPanel from '../components/AgreementPanel';
import { SlidersHorizontal, Activity, ListChecks, ArrowRight } from 'lucide-react';

export default function Dashboard({ metrics, onNavigate }) {
  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <MetricCards metrics={metrics} />

      {/* Production Statistical Data Drift Monitoring Panel */}
      <DriftPanel />

      {/* Human Analyst Agreement & Operational Trust Monitor */}
      <AgreementPanel />

      {/* Feature Quick-Access Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Optimizer Card */}
        <div 
          onClick={() => onNavigate('optimizer')}
          className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-slate-300 transition cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center mb-4">
              <SlidersHorizontal className="w-5 h-5 text-blue-700" />
            </div>
            <h3 className="text-base font-bold text-slate-800 group-hover:text-blue-700 transition">
              Threshold Optimizer
            </h3>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Fine-tune decision risk cutoff thresholds to minimize financial loss between operational checks and dispute costs.
            </p>
          </div>
          <div className="mt-5 flex items-center text-xs font-bold text-blue-700 group-hover:translate-x-1 transition-transform">
            Open Optimizer & Chart <ArrowRight className="w-4 h-4 ml-1" />
          </div>
        </div>

        {/* Risk Assessment Card */}
        <div 
          onClick={() => onNavigate('assessment')}
          className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-slate-300 transition cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center mb-4">
              <Activity className="w-5 h-5 text-blue-700" />
            </div>
            <h3 className="text-base font-bold text-slate-800 group-hover:text-blue-700 transition">
              Risk Assessment Console
            </h3>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Evaluate live transaction parameters and generate real-time AI risk scores with full explainability.
            </p>
          </div>
          <div className="mt-5 flex items-center text-xs font-bold text-blue-700 group-hover:translate-x-1 transition-transform">
            Launch Risk Console <ArrowRight className="w-4 h-4 ml-1" />
          </div>
        </div>

        {/* Review Queue Card */}
        <div 
          onClick={() => onNavigate('queue')}
          className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-slate-300 transition cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center mb-4">
              <ListChecks className="w-5 h-5 text-blue-700" />
            </div>
            <h3 className="text-base font-bold text-slate-800 group-hover:text-blue-700 transition">
              Audit Review Queue
            </h3>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Review flagged high-risk transactions, perform audit checks, and submit analyst review decisions.
            </p>
          </div>
          <div className="mt-5 flex items-center text-xs font-bold text-blue-700 group-hover:translate-x-1 transition-transform">
            View Audit Queue <ArrowRight className="w-4 h-4 ml-1" />
          </div>
        </div>
      </div>

      {/* System Overview Card — Clean Banking Overview */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">
          Risk Management System Overview
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="font-semibold text-slate-800">Scoring Engine</div>
            <div className="text-slate-500 mt-1">Real-Time Machine Learning Transaction Analysis</div>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="font-semibold text-slate-800">Audit Compliance</div>
            <div className="text-slate-500 mt-1">Full SHAP Factor Attribution on Every Decision</div>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="font-semibold text-slate-800">Operational Feedback</div>
            <div className="text-slate-500 mt-1">Human-Analyst Overturn & Agreement Tracking Loop</div>
          </div>
        </div>
      </div>
    </div>
  );
}
