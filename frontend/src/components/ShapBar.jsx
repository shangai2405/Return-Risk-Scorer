import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

export default function ShapBar({ factorDetails }) {
  if (!factorDetails || factorDetails.length === 0) return null;
  const maxShap = Math.max(...factorDetails.map(f => Math.abs(f.shap_value)), 0.001);

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm relative">
      <div className="h-1.5 w-full" style={{ background: 'linear-gradient(90deg, #0f2d5c, #3b82f6)' }} />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1">
            SHAP Explainability
            <InfoTooltip text="SHAP values show exactly which features drove this score. Red bars increase risk; green bars decrease risk." />
          </h3>
          <span className="text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded bg-slate-100 text-slate-500 border border-slate-200">
            Top 3 Factors
          </span>
        </div>

        <div className="space-y-4">
          {factorDetails.map((factor, idx) => {
            const isPos = factor.shap_value > 0;
            const width = Math.min(100, (Math.abs(factor.shap_value) / maxShap) * 100);

            return (
              <div key={idx}>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                    {isPos
                      ? <TrendingUp className="w-3.5 h-3.5 text-red-500 shrink-0" />
                      : <TrendingDown className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    }
                    {factor.label}
                    <InfoTooltip text={isPos
                      ? `Increased return risk by ${Math.abs(factor.shap_value).toFixed(3)} SHAP points.`
                      : `Decreased return risk by ${Math.abs(factor.shap_value).toFixed(3)} SHAP points.`
                    } />
                  </span>
                  <span className={`font-bold font-mono ml-2 ${isPos ? 'text-red-500' : 'text-emerald-600'}`}>
                    {isPos ? '+' : ''}{factor.shap_value.toFixed(3)}
                  </span>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${isPos ? 'bg-red-400' : 'bg-emerald-400'}`}
                    style={{ width: `${width}%` }}
                  />
                </div>
                <div className="text-[10px] text-slate-400 mt-1">
                  {isPos ? '↑ Increases return probability' : '↓ Reduces return probability'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
