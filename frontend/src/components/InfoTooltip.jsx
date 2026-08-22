import React from 'react';
import { HelpCircle } from 'lucide-react';

export function InfoTooltip({ text, position = 'bottom', align = 'left' }) {
  const isTop = position === 'top';
  const isRight = align === 'right';

  let alignClasses = 'left-1/2 -translate-x-1/2 sm:left-0 sm:translate-x-0';
  let arrowClasses = 'left-1/2 -ml-1 sm:left-3 sm:ml-0';

  if (isRight) {
    alignClasses = 'right-0 left-auto translate-x-0';
    arrowClasses = 'right-3 left-auto';
  } else if (align === 'center') {
    alignClasses = 'left-1/2 -translate-x-1/2';
    arrowClasses = 'left-1/2 -ml-1';
  }

  return (
    <span className="group relative inline-flex items-center cursor-help ml-1 align-middle">
      <HelpCircle className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600 transition shrink-0" />
      <span className={`pointer-events-none absolute w-56 rounded-lg bg-slate-900 p-2.5 text-[11px] font-normal text-slate-100 shadow-2xl border border-slate-700 opacity-0 group-hover:opacity-100 transition-all duration-150 z-[9999] leading-normal text-left ${
        isTop
          ? `bottom-full mb-2 ${alignClasses}`
          : `top-full mt-2 ${alignClasses}`
      }`}>
        {text}
        <span className={`absolute border-4 border-transparent ${
          isTop
            ? `top-full border-t-slate-900 ${arrowClasses}`
            : `bottom-full border-b-slate-900 ${arrowClasses}`
        }`} />
      </span>
    </span>
  );
}
