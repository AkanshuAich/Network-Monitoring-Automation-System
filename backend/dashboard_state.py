"""
Dashboard State — Thread-safe in-memory store for host health data.

Tracks per-host status, latency history (ring buffer), health scores,
and provides aggregate metrics for the dashboard.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Optional

from models import (
    Alert,
    AlertSeverity,
    HealthMetrics,
    HostConfig,
    HostStatus,
    HostStatusEnum,
    TCPHandshakeLog,
)

logger = logging.getLogger("dashboard_state")


class DashboardState:
    """Central in-memory data store for all monitored hosts."""

    def __init__(self, max_latency_history: int = 100) -> None:
        self._hosts: dict[str, HostStatus] = {}
        self._latency_buffers: dict[str, deque[float]] = {}
        self._alerts: list[Alert] = []
        self._max_history = max_latency_history
        self._lock = asyncio.Lock()
        self._subscribers: list[asyncio.Queue[dict]] = []

    # ── Host Registration ────────────────────────────────────────────────

    async def register_host(self, config: HostConfig) -> HostStatus:
        """Add a host to the monitoring pool."""
        async with self._lock:
            status = HostStatus(
                id=config.id,
                name=config.name,
                host=config.host,
                port=config.port,
            )
            self._hosts[config.id] = status
            self._latency_buffers[config.id] = deque(maxlen=self._max_history)
            logger.info("Registered host %s (%s:%s)", config.name, config.host, config.port)
            return status

    # ── Updates ──────────────────────────────────────────────────────────

    async def update_host(
        self,
        host_id: str,
        *,
        success: bool,
        latency_ms: float,
        handshake_logs: list[TCPHandshakeLog] | None = None,
    ) -> HostStatus:
        """Record a new check result and recalculate health score."""
        async with self._lock:
            host = self._hosts.get(host_id)
            if host is None:
                raise KeyError(f"Unknown host id: {host_id}")

            host.last_checked = datetime.utcnow()
            host.latency_ms = latency_ms

            if success:
                host.status = HostStatusEnum.UP
                host.failure_count = 0
                buf = self._latency_buffers[host_id]
                buf.append(latency_ms)
                host.latency_history = list(buf)
            else:
                host.failure_count += 1
                host.status = HostStatusEnum.DOWN

            if handshake_logs:
                # Keep last 20 handshake logs
                host.handshake_logs = (host.handshake_logs + handshake_logs)[-20:]

            host.health_score = self._calculate_health(host)

            # Broadcast to WebSocket subscribers
            await self._broadcast(host)

            return host

    # ── Health Score ─────────────────────────────────────────────────────

    @staticmethod
    def _calculate_health(host: HostStatus) -> float:
        """
        Weighted health score  (0-100):
            Uptime component   60 %
            Latency component  25 %
            Failure component  15 %
        """
        # Uptime — binary
        uptime = 100.0 if host.status == HostStatusEnum.UP else 0.0

        # Latency — lower is better; 0 ms → 100, ≥2 000 ms → 0
        if host.latency_ms is not None and host.latency_ms >= 0:
            latency_score = max(0.0, 100.0 - (host.latency_ms / 20.0))
        else:
            latency_score = 0.0

        # Failures
        failure_score = max(0.0, 100.0 - host.failure_count * 25.0)

        score = uptime * 0.60 + latency_score * 0.25 + failure_score * 0.15
        return round(min(100.0, max(0.0, score)), 1)

    # ── Queries ──────────────────────────────────────────────────────────

    async def get_all_hosts(self) -> list[HostStatus]:
        async with self._lock:
            return list(self._hosts.values())

    async def get_host(self, host_id: str) -> Optional[HostStatus]:
        async with self._lock:
            return self._hosts.get(host_id)

    async def get_metrics(self) -> HealthMetrics:
        async with self._lock:
            hosts = list(self._hosts.values())
            up = sum(1 for h in hosts if h.status == HostStatusEnum.UP)
            down = sum(1 for h in hosts if h.status == HostStatusEnum.DOWN)
            unknown = sum(1 for h in hosts if h.status == HostStatusEnum.UNKNOWN)
            latencies = [h.latency_ms for h in hosts if h.latency_ms is not None and h.status == HostStatusEnum.UP]
            avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None
            total = len(hosts)
            uptime_pct = round((up / total) * 100, 1) if total else 100.0

            return HealthMetrics(
                total_hosts=total,
                hosts_up=up,
                hosts_down=down,
                hosts_unknown=unknown,
                average_latency_ms=avg_latency,
                uptime_percentage=uptime_pct,
                last_updated=datetime.utcnow(),
            )

    # ── Alerts ───────────────────────────────────────────────────────────

    async def add_alert(self, alert: Alert) -> None:
        async with self._lock:
            self._alerts.append(alert)
            logger.warning("ALERT [%s] %s — %s", alert.severity.value, alert.host_name, alert.message)

    async def get_alerts(self, severity: Optional[AlertSeverity] = None) -> list[Alert]:
        async with self._lock:
            if severity:
                return [a for a in self._alerts if a.severity == severity]
            return list(self._alerts)

    # ── WebSocket Pub/Sub ────────────────────────────────────────────────

    def subscribe(self) -> asyncio.Queue[dict]:
        """Return a new queue that will receive live host updates."""
        q: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict]) -> None:
        self._subscribers = [s for s in self._subscribers if s is not q]

    async def _broadcast(self, host: HostStatus) -> None:
        """Push a host-status update to every subscriber (non-blocking)."""
        msg = host.model_dump(mode="json")
        dead: list[asyncio.Queue[dict]] = []
        for q in self._subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)
