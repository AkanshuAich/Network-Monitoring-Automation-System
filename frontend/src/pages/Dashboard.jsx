import React, { useEffect, useState, useCallback } from 'react';
import { fetchHosts, fetchMetrics, addHost } from '../services/api';
import socketService from '../services/socket';
import HostCard from '../components/HostCard';
import MetricCard from '../components/MetricCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

export default function Dashboard() {
    const [hosts, setHosts] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showAdd, setShowAdd] = useState(false);
    const [newHost, setNewHost] = useState({ name: '', host: '', port: 80 });

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [h, m] = await Promise.all([fetchHosts(), fetchMetrics()]);
            setHosts(h);
            setMetrics(m);
        } catch (err) {
            setError(err.message || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        socketService.connect();
        const unsub = socketService.subscribe((update) => {
            setHosts((prev) =>
                prev.map((h) => (h.id === update.id ? { ...h, ...update } : h))
            );
        });
        return () => {
            unsub();
            socketService.disconnect();
        };
    }, [load]);

    const handleAddHost = async (e) => {
        e.preventDefault();
        try {
            const created = await addHost(newHost);
            setHosts((prev) => [...prev, created]);
            setNewHost({ name: '', host: '', port: 80 });
            setShowAdd(false);
        } catch {
            /* silently handle */
        }
    };

    if (loading) return <LoadingSpinner text="Loading dashboard…" />;
    if (error) return <ErrorBanner message={error} onRetry={load} />;

    return (
        <div className="animate-fade-in">
            {/* Metrics Row */}
            {metrics && (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <MetricCard label="Total Hosts" value={metrics.total_hosts} icon="🖥️" color="brand" />
                    <MetricCard label="Hosts Up" value={metrics.hosts_up} icon="✅" color="emerald" />
                    <MetricCard label="Hosts Down" value={metrics.hosts_down} icon="❌" color="red" />
                    <MetricCard
                        label="Avg Latency"
                        value={metrics.average_latency_ms != null ? `${metrics.average_latency_ms} ms` : '—'}
                        icon="⚡"
                        color="amber"
                    />
                </div>
            )}

            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-xl font-bold text-white">Monitored Hosts</h1>
                <button
                    onClick={() => setShowAdd(!showAdd)}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition-colors duration-200 flex items-center gap-2"
                >
                    <span className="text-lg leading-none">+</span> Add Host
                </button>
            </div>

            {/* Add Host Form */}
            {showAdd && (
                <form onSubmit={handleAddHost} className="glass-card p-5 mb-6 animate-slide-up">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <input
                            type="text"
                            placeholder="Name"
                            required
                            value={newHost.name}
                            onChange={(e) => setNewHost({ ...newHost, name: e.target.value })}
                            className="w-full px-4 py-2.5 rounded-xl bg-surface-700/60 border border-white/10 text-white text-sm placeholder:text-surface-200 focus:outline-none focus:border-brand-500/50 transition"
                        />
                        <input
                            type="text"
                            placeholder="Host / IP"
                            required
                            value={newHost.host}
                            onChange={(e) => setNewHost({ ...newHost, host: e.target.value })}
                            className="w-full px-4 py-2.5 rounded-xl bg-surface-700/60 border border-white/10 text-white text-sm placeholder:text-surface-200 focus:outline-none focus:border-brand-500/50 transition"
                        />
                        <div className="flex gap-3">
                            <input
                                type="number"
                                placeholder="Port"
                                value={newHost.port}
                                onChange={(e) => setNewHost({ ...newHost, port: parseInt(e.target.value) || 80 })}
                                className="w-full px-4 py-2.5 rounded-xl bg-surface-700/60 border border-white/10 text-white text-sm placeholder:text-surface-200 focus:outline-none focus:border-brand-500/50 transition"
                            />
                            <button
                                type="submit"
                                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium whitespace-nowrap transition-colors"
                            >
                                Save
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowAdd(false)}
                                className="px-5 py-2.5 rounded-xl bg-surface-600 hover:bg-surface-500 text-white text-sm font-medium whitespace-nowrap transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </form>
            )}

            {/* Host Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {hosts.map((host) => (
                    <HostCard key={host.id} host={host} />
                ))}
                {hosts.length === 0 && (
                    <div className="col-span-full text-center py-16 text-surface-200">
                        <p className="text-4xl mb-3">📡</p>
                        <p className="text-sm">No hosts are being monitored yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
