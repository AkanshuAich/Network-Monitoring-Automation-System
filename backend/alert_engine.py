"""
Alert Engine — Threshold-based alerting with retries and exponential backoff.

Evaluates check results against configured thresholds and emits
WARNING / CRITICAL alerts.  Optionally posts to a Slack webhook.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aiohttp

from dashboard_state import DashboardState
from models import Alert, AlertConfig, AlertSeverity, HostStatus, HostStatusEnum, SlackConfig

logger = logging.getLogger("alert_engine")


class AlertEngine:
    """Evaluates host check results and fires alerts when thresholds are breached."""

    def __init__(
        self,
        state: DashboardState,
        config: AlertConfig,
        slack: SlackConfig | None = None,
    ) -> None:
        self._state = state
        self._cfg = config
        self._slack = slack
        # Track per-host consecutive failure counts independently so
        # we don't double-alert on the same streak.
        self._alerted_streaks: dict[str, int] = {}

    # ── Public Interface ─────────────────────────────────────────────────

    async def evaluate(self, host: HostStatus) -> Optional[Alert]:
        """
        Evaluate the latest status of a host and create an alert if warranted.

        Returns the ``Alert`` that was created, or ``None``.
        """
        alert: Optional[Alert] = None

        # ── CRITICAL: consecutive failures exceeded ──────────────────
        if (
            host.status == HostStatusEnum.DOWN
            and host.failure_count >= self._cfg.consecutive_failures
        ):
            last_alerted = self._alerted_streaks.get(host.id, 0)
            if host.failure_count > last_alerted:
                alert = Alert(
                    host_id=host.id,
                    host_name=host.name,
                    severity=AlertSeverity.CRITICAL,
                    message=(
                        f"Host {host.name} ({host.host}:{host.port}) is DOWN — "
                        f"{host.failure_count} consecutive failures"
                    ),
                )
                self._alerted_streaks[host.id] = host.failure_count

        # ── WARNING: latency above threshold ─────────────────────────
        elif (
            host.status == HostStatusEnum.UP
            and host.latency_ms is not None
            and host.latency_ms > self._cfg.latency_warning_ms
        ):
            severity = (
                AlertSeverity.CRITICAL
                if host.latency_ms > self._cfg.latency_critical_ms
                else AlertSeverity.WARNING
            )
            alert = Alert(
                host_id=host.id,
                host_name=host.name,
                severity=severity,
                message=(
                    f"High latency on {host.name}: {host.latency_ms:.1f} ms "
                    f"(threshold: {self._cfg.latency_warning_ms} ms)"
                ),
            )

        # Reset streak tracker when host recovers
        if host.status == HostStatusEnum.UP and host.id in self._alerted_streaks:
            del self._alerted_streaks[host.id]

        if alert:
            await self._state.add_alert(alert)
            await self._notify_slack(alert)

        return alert

    # ── Retry with Exponential Backoff ───────────────────────────────────

    async def retry_check(
        self,
        check_fn,
        host: str,
        port: int,
        timeout: float,
    ):
        """
        Retry a TCP check with exponential backoff.

        *check_fn* should be ``tcp_check`` or a compatible coroutine.
        Returns the last ``TCPCheckResult``.
        """
        attempts = self._cfg.retry_attempts
        backoff = self._cfg.backoff_base

        for attempt in range(1, attempts + 1):
            result = await check_fn(host, port, timeout=timeout)
            if result.success:
                return result
            wait = min(backoff * (2 ** (attempt - 1)), self._cfg.backoff_max)
            logger.info(
                "Retry %d/%d for %s:%s in %.1f s",
                attempt, attempts, host, port, wait,
            )
            await asyncio.sleep(wait)

        # Final attempt
        return await check_fn(host, port, timeout=timeout)

    # ── Slack Notification ───────────────────────────────────────────────

    async def _notify_slack(self, alert: Alert) -> None:
        """Post alert to Slack webhook if configured."""
        if not self._slack or not self._slack.enabled or not self._slack.webhook_url:
            return

        emoji = "🔴" if alert.severity == AlertSeverity.CRITICAL else "🟡"
        payload = {
            "text": f"{emoji} *[{alert.severity.value}]* {alert.message}",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._slack.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        logger.error("Slack webhook returned %s", resp.status)
        except Exception as exc:
            logger.error("Slack notification failed: %s", exc)
