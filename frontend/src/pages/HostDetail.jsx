import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart,
} from 'recharts';
import { fetchHost, fetchAlerts } from '../services/api';
import socketService from '../services/socket';
import StatusBadge from '../components/StatusBadge';
import HealthBar from '../components/HealthBar';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

export default function HostDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [host, setHost] = useState(null);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showHandshake, setShowHandshake] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [h, a] = await Promise.all([fetchHost(id), fetchAlerts()]);
            setHost(h);
            setAlerts(a.filter((al) => al.host_id === id));
        } catch (err) {
            setError(err.message || 'Failed to load host data');
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        load();
        socketService.connect();
        const unsub = socketService.subscribe((update) => {
            if (update.id === id) setHost((prev) => ({ ...prev, ...update }));
        });
        return () => {
            unsub();
            socketService.disconnect();
        };
    }, [id, load]);

    if (loading) return <LoadingSpinner text="Loading host details…" />;
    if (error) return <ErrorBanner message={error} onRetry={load} />;
    if (!host) return null;

    // Prepare latency chart data
    const chartData = (host.latency_history || []).map((val, i) => ({
        idx: i + 1,
        latency: val,
    }));

    return (
        <div className="animate-fade-in">
            {/* Back Button */}
            <button
                onClick={() => navigate('/')}
                className="mb-6 text-sm text-surface-200 hover:text-white flex items-center gap-2 transition-colors"
            >
                ← Back to Dashboard
            </button>

            {/* Header Card */}
            <div className="glass-card p-6 mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-white">{host.name}</h1>
                        <p className="text-sm text-surface-200 font-mono mt-1">
                            {host.host}:{host.port}
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <StatusBadge status={host.status} />
                        <span className="text-3xl font-extrabold text-white">
                            {host.latency_ms != null ? `${host.latency_ms.toFixed(1)} ms` : '—'}
                        </span>
                    </div>
                </div>
                <div className="mt-5 max-w-xs">
                    <HealthBar score={host.health_score} />
                </div>
                <div className="mt-4 flex flex-wrap gap-6 text-xs text-surface-200">
                    <span>Failures: <strong className="text-white">{host.failure_count}</strong></span>
                    <span>
                        Last Checked:{' '}
                        <strong className="text-white">
                            {host.last_checked ? new Date(host.last_checked).toLocaleString() : 'Never'}
                        </strong>
                    </span>
                </div>
            </div>

            {/* Latency Chart */}
            <div className="glass-card p-6 mb-6">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
                    Latency Trend
                </h2>
                {chartData.length > 1 ? (
                    <ResponsiveContainer width="100%" height={260}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="latGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="idx" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} />
                            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} unit=" ms" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1e293b',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: 12,
                                    fontSize: 12,
                                }}
                                labelStyle={{ color: '#94a3b8' }}
                            />
                            <Area
                                type="monotone"
                                dataKey="latency"
                                stroke="#6366f1"
                                strokeWidth={2}
                                fill="url(#latGrad)"
                                dot={false}
                                activeDot={{ r: 4, fill: '#a5b4fc' }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <p className="text-sm text-surface-200 text-center py-10">
                        Not enough data points for a chart yet.
                    </p>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Alert Timeline */}
                <div className="glass-card p-6">
                    <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
                        Alert Timeline
                    </h2>
                    {alerts.length === 0 ? (
                        <p className="text-sm text-surface-200 text-center py-6">No alerts for this host.</p>
                    ) : (
                        <div className="space-y-3 max-h-72 overflow-y-auto pr-2">
                            {alerts.map((a) => (
                                <div
                                    key={a.id}
                                    className="flex items-start gap-3 p-3 rounded-xl bg-surface-700/40"
                                >
                                    <span
                                        className={`mt-0.5 status-dot ${a.severity === 'CRITICAL' ? 'status-dot-down' : 'status-dot-unknown'
                                            }`}
                                    />
                                    <div className="min-w-0">
                                        <p className="text-xs text-white font-medium">{a.message}</p>
                                        <p className="text-[10px] text-surface-200 mt-0.5">
                                            {new Date(a.timestamp).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* TCP Handshake Debug Logs */}
                <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                            TCP Handshake Logs
                        </h2>
                        <button
                            onClick={() => setShowHandshake(!showHandshake)}
                            className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                        >
                            {showHandshake ? 'Hide' : 'Show'}
                        </button>
                    </div>
                    {showHandshake && (
                        <div className="space-y-2 max-h-72 overflow-y-auto pr-2 animate-slide-up">
                            {(host.handshake_logs || []).length === 0 ? (
                                <p className="text-sm text-surface-200 text-center py-6">No handshake logs yet.</p>
                            ) : (
                                host.handshake_logs.map((log, i) => (
                                    <div
                                        key={i}
                                        className="flex items-start gap-3 p-3 rounded-xl bg-surface-700/40 font-mono text-xs"
                                    >
                                        <span
                                            className={`badge text-[10px] ${log.step === 'FAIL' ? 'badge-critical' : 'badge-up'
                                                }`}
                                        >
                                            {log.step}
                                        </span>
                                        <div className="min-w-0">
                                            <p className="text-surface-200">{log.message}</p>
                                            <p className="text-[10px] text-surface-200/60 mt-0.5">
                                                {log.elapsed_ms.toFixed(2)} ms
                                            </p>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
