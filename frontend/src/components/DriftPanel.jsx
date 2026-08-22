import React, { useState, useEffect } from 'react';
import { fetchDriftStatus } from '../api/client';
import { InfoTooltip } from './InfoTooltip';
import { Activity, ShieldCheck, AlertTriangle, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';

export default function DriftPanel() {
  const [driftData, setDriftData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [showOnlyShifted, setShowOnlyShifted] = useState(true);
  const [error, setError] = useState(null);

  const loadDrift = async () => {
    setLoading(true); setError(null);
    try {
      const data = await fetchDriftStatus();
      setDriftData(data);
    } catch (err) {
      setError(err.message || 'Could not fetch statistical drift status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDrift(); }, []);

  if (loading) return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm mb-6 flex items-center justify-between">
      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
        <RefreshCw className="w-4 h-4 animate-spin text-blue-700" />
        Evaluating production statistical data drift (KS Test & PSI)...
      </div>
    </div>
  );

  if (error || !driftData) return null;

  const isDrift = driftData.overall_status === 'DRIFT_DETECTED';
  const shiftedCount = driftData.drift_feature_count || 0;
  const allFeatures = driftData.features || [];
  
  const displayedFeatures = showOnlyShifted && shiftedCount > 0
    ? allFeatures.filter(f => f.drift_detected)
    : allFeatures;

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm mb-6 relative">
      {/* Top status bar */}
      <div className={`h-1.5 w-full rounded-t-xl ${isDrift ? 'bg-amber-500' : 'bg-emerald-500'}`} />

      {/* Main compact card header */}
      <div className="px-5 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center border shrink-0 ${
            isDrift ? 'bg-amber-50 border-amber-200 text-amber-600' : 'bg-emerald-50 border-emerald-200 text-emerald-600'
          }`}>
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Production Data Drift Monitor
              </h3>
              <InfoTooltip text="Out-of-band statistical monitor (KS Test for numeric features, PSI for categorical features). Detects if production input distributions deviate from training data without modifying scoring." />
            </div>
            <p className="text-[11px] text-slate-400">
              Window: {driftData.window_size} orders &nbsp;·&nbsp; Read-only statistical control
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Compact Status Badge */}
          {isDrift ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              Drift Detected ({shiftedCount} shifted)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              Distributions Stable
            </span>
          )}

          {/* Expand toggle */}
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 px-3 py-1 text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition"
          >
            {expanded ? <>Hide <ChevronUp className="w-3.5 h-3.5" /></> : <>View Details <ChevronDown className="w-3.5 h-3.5" /></>}
          </button>
        </div>
      </div>

      {/* Expandable compact breakdown panel */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50/60 p-4 rounded-b-xl">
          <div className="flex items-center justify-between mb-3 text-xs">
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">
              Statistical Test Results ({displayedFeatures.length})
            </span>

            {/* Filter Toggle */}
            <div className="flex bg-slate-200/70 p-0.5 rounded-lg text-[11px] font-semibold">
              <button
                onClick={() => setShowOnlyShifted(true)}
                className={`px-2.5 py-1 rounded-md transition ${
                  showOnlyShifted ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Shifted Only ({shiftedCount})
              </button>
              <button
                onClick={() => setShowOnlyShifted(false)}
                className={`px-2.5 py-1 rounded-md transition ${
                  !showOnlyShifted ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                All Features ({allFeatures.length})
              </button>
            </div>
          </div>

          {/* Compact 2-Column Grid Container with Max Height Scroll */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-56 overflow-y-auto pr-1">
            {displayedFeatures.map((feat, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-xs bg-white flex flex-col justify-between ${
                  feat.drift_detected ? 'border-amber-300 bg-amber-50/20' : 'border-slate-200'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <span className="font-mono font-bold text-slate-800 truncate">{feat.feature}</span>
                  {feat.drift_detected ? (
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 shrink-0 border border-amber-200">
                      Shifted
                    </span>
                  ) : (
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-500 shrink-0">
                      Normal
                    </span>
                  )}
                </div>

                <div className="text-[11px] text-slate-500 line-clamp-2 mb-1.5">
                  {feat.explanation}
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono border-t border-slate-100 pt-1.5 mt-auto">
                  <span>Test: {feat.metric_type} ({feat.threshold})</span>
                  <span className="font-bold text-slate-700">Val: {feat.metric_value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
