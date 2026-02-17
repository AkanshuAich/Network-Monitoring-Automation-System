import React from 'react';

export default function MetricCard({ label, value, sub, icon, color = 'brand' }) {
    const colorMap = {
        brand: 'from-brand-500/15 to-brand-600/5   border-brand-500/15   text-brand-400',
        emerald: 'from-emerald-500/15 to-emerald-600/5 border-emerald-500/15 text-emerald-400',
        red: 'from-red-500/15 to-red-600/5       border-red-500/15     text-red-400',
        amber: 'from-amber-500/15 to-amber-600/5   border-amber-500/15   text-amber-400',
    };
    const cls = colorMap[color] || colorMap.brand;

    return (
        <div className={`glass-card bg-gradient-to-br ${cls} p-5 animate-slide-up`}>
            <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-surface-200">
                    {label}
                </span>
                <span className="text-lg">{icon}</span>
            </div>
            <p className="text-3xl font-extrabold text-white tracking-tight">
                {value}
            </p>
            {sub && <p className="text-xs text-surface-200 mt-1">{sub}</p>}
        </div>
    );
}
