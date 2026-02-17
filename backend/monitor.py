"""
Monitoring Engine — Async loop that continuously checks all registered hosts.

Uses ``tcp_analyzer.tcp_check`` for probes, updates ``DashboardState``,
and delegates threshold evaluation to ``AlertEngine``.
Supports graceful shutdown via an ``asyncio.Event``.
"""

from __future__ import annotations

import asyncio
import logging

from alert_engine import AlertEngine
from dashboard_state import DashboardState
from models import AppConfig, HostConfig
from tcp_analyzer import tcp_check

logger = logging.getLogger("monitor")


class MonitorEngine:
    """Orchestrates periodic health checks for every registered host."""

    def __init__(
        self,
        config: AppConfig,
        state: DashboardState,
        alert_engine: AlertEngine,
    ) -> None:
        self._cfg = config
        self._state = state
        self._alert_engine = alert_engine
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Register configured hosts and kick off the monitoring loop."""
        for hc in self._cfg.hosts:
            await self._state.register_host(hc)
        self._task = asyncio.create_task(self._run(), name="monitor-loop")
        logger.info(
            "Monitor engine started — %d hosts, interval %d s",
            len(self._cfg.hosts),
            self._cfg.monitoring.check_interval,
        )

    async def stop(self) -> None:
        """Signal the loop to stop and wait for clean shutdown."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Monitor engine stopped.")

    # ── Add Host Dynamically ─────────────────────────────────────────────

    async def add_host(self, host_config: HostConfig) -> None:
        """Register a new host to the monitoring pool at runtime."""
        self._cfg.hosts.append(host_config)
        await self._state.register_host(host_config)
        logger.info("Dynamically added host %s (%s:%s)", host_config.name, host_config.host, host_config.port)

    # ── Main Loop ────────────────────────────────────────────────────────

    async def _run(self) -> None:
        """Infinite loop: check all hosts concurrently, sleep, repeat."""
        while not self._stop_event.is_set():
            try:
                hosts = await self._state.get_all_hosts()
                # Fan-out: check every host concurrently
                await asyncio.gather(
                    *(self._check_host(h.id, h.host, h.port) for h in hosts),
                    return_exceptions=True,
                )
            except Exception as exc:
                logger.exception("Unexpected error in monitor loop: %s", exc)

            # Sleep in small increments so we can respond to stop quickly
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._cfg.monitoring.check_interval,
                )
                break  # stop_event was set
            except asyncio.TimeoutError:
                pass  # interval elapsed — loop again

    async def _check_host(self, host_id: str, host: str, port: int) -> None:
        """Run a single host probe with retries, update state, evaluate alerts."""
        timeout = self._cfg.monitoring.timeout

        # First attempt
        result = await tcp_check(host, port, timeout=timeout)

        # Retry on failure
        if not result.success:
            result = await self._alert_engine.retry_check(
                tcp_check, host, port, timeout=timeout,
            )

        # Persist
        updated = await self._state.update_host(
            host_id,
            success=result.success,
            latency_ms=result.latency_ms,
            handshake_logs=result.handshake_logs,
        )

        # Evaluate alert thresholds
        await self._alert_engine.evaluate(updated)
