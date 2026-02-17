import React from 'react';

export default function HealthBar({ score = 0 }) {
    const pct = Math.max(0, Math.min(100, score));

    const color =
        pct >= 80 ? 'from-emerald-400 to-emerald-500' :
            pct >= 50 ? 'from-amber-400 to-amber-500' :
                'from-red-400 to-red-500';

    return (
        <div className="w-full">
            <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-medium text-surface-200 uppercase tracking-wider">
                    Health
                </span>
                <span className="text-xs font-bold text-white">{pct.toFixed(1)}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-surface-700/80 overflow-hidden">
                <div
                    className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700 ease-out`}
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    );
}
