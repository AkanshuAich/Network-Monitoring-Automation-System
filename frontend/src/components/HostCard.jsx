import React from 'react';
import StatusBadge from './StatusBadge';
import HealthBar from './HealthBar';
import { useNavigate } from 'react-router-dom';

export default function HostCard({ host }) {
    const navigate = useNavigate();

    const latency = host.latency_ms != null ? `${host.latency_ms.toFixed(1)} ms` : '—';
    const lastChecked = host.last_checked
        ? new Date(host.last_checked).toLocaleTimeString()
        : 'Never';

    return (
        <div
            onClick={() => navigate(`/hosts/${host.id}`)}
            className="glass-card p-5 cursor-pointer group animate-slide-up hover:scale-[1.02] active:scale-[0.98]"
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
                <div className="min-w-0">
                    <h3 className="text-sm font-bold text-white truncate group-hover:text-brand-300 transition-colors">
                        {host.name}
                    </h3>
                    <p className="text-xs text-surface-200 font-mono mt-0.5 truncate">
                        {host.host}:{host.port}
                    </p>
                </div>
                <StatusBadge status={host.status} />
            </div>

            {/* Latency */}
            <div className="flex items-baseline gap-1 mb-4">
                <span className="text-2xl font-extrabold text-white tracking-tight">{latency}</span>
            </div>

            {/* Health Bar */}
            <HealthBar score={host.health_score} />

            {/* Footer */}
            <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-[10px] text-surface-200 uppercase tracking-widest">Last check</span>
                <span className="text-xs text-surface-200 font-mono">{lastChecked}</span>
            </div>
        </div>
    );
}
