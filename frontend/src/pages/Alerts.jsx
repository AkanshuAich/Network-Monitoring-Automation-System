import React, { useEffect, useState, useCallback } from 'react';
import { fetchAlerts } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

const FILTERS = ['ALL', 'WARNING', 'CRITICAL'];

export default function Alerts() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('ALL');

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchAlerts(filter === 'ALL' ? undefined : filter);
            setAlerts(data);
        } catch (err) {
            setError(err.message || 'Failed to load alerts');
        } finally {
            setLoading(false);
        }
    }, [filter]);

    useEffect(() => {
        load();
    }, [load]);

    if (loading) return <LoadingSpinner text="Loading alerts…" />;
    if (error) return <ErrorBanner message={error} onRetry={load} />;

    return (
        <div className="animate-fade-in">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
                <h1 className="text-xl font-bold text-white">Alerts</h1>

                {/* Filter Toggle */}
                <div className="flex bg-surface-700/60 rounded-xl p-1 gap-1">
                    {FILTERS.map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${filter === f
                                    ? 'bg-brand-600 text-white shadow'
                                    : 'text-surface-200 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* Alert List */}
            {alerts.length === 0 ? (
                <div className="text-center py-20 text-surface-200">
                    <p className="text-4xl mb-3">🔔</p>
                    <p className="text-sm">No alerts to display.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {alerts.map((alert) => (
                        <div
                            key={alert.id}
                            className="glass-card p-5 flex flex-col sm:flex-row sm:items-center gap-4 animate-slide-up"
                        >
                            {/* Severity Badge */}
                            <span
                                className={`badge ${alert.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning'
                                    }`}
                            >
                                {alert.severity}
                            </span>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <p className="text-sm text-white font-medium">{alert.message}</p>
                                <p className="text-xs text-surface-200 mt-1">
                                    Host: <span className="font-semibold text-white">{alert.host_name}</span>
                                </p>
                            </div>

                            {/* Timestamp */}
                            <span className="text-xs text-surface-200 font-mono whitespace-nowrap">
                                {new Date(alert.timestamp).toLocaleString()}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
