/**
 * REST API service — Axios instance and endpoint wrappers.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
});

// ── Hosts ─────────────────────────────────────────────────────────────────

export const fetchHosts = () => api.get('/hosts').then(r => r.data);

export const fetchHost = (id) => api.get(`/hosts/${id}`).then(r => r.data);

export const addHost = (payload) => api.post('/hosts', payload).then(r => r.data);

// ── Alerts ────────────────────────────────────────────────────────────────

export const fetchAlerts = (severity) => {
    const params = severity ? { severity } : {};
    return api.get('/alerts', { params }).then(r => r.data);
};

// ── Metrics ───────────────────────────────────────────────────────────────

export const fetchMetrics = () => api.get('/metrics').then(r => r.data);

export default api;
