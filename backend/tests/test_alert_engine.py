"""Tests for Alert Engine."""

import pytest

from alert_engine import AlertEngine
from dashboard_state import DashboardState
from models import AlertConfig, AlertSeverity, HostStatus, HostStatusEnum


@pytest.fixture
def state():
    return DashboardState()


@pytest.fixture
def alert_cfg():
    return AlertConfig(
        latency_warning_ms=100,
        latency_critical_ms=500,
        consecutive_failures=3,
        retry_attempts=1,
        backoff_base=0.01,
        backoff_max=0.05,
    )


@pytest.fixture
def engine(state, alert_cfg):
    return AlertEngine(state=state, config=alert_cfg)


@pytest.mark.asyncio
async def test_no_alert_when_healthy(engine):
    host = HostStatus(
        id="h1", name="Test", host="1.2.3.4", port=80,
        status=HostStatusEnum.UP, latency_ms=50.0,
    )
    alert = await engine.evaluate(host)
    assert alert is None


@pytest.mark.asyncio
async def test_warning_on_high_latency(engine, state):
    host = HostStatus(
        id="h1", name="Test", host="1.2.3.4", port=80,
        status=HostStatusEnum.UP, latency_ms=200.0,
    )
    alert = await engine.evaluate(host)
    assert alert is not None
    assert alert.severity == AlertSeverity.WARNING


@pytest.mark.asyncio
async def test_critical_on_very_high_latency(engine, state):
    host = HostStatus(
        id="h1", name="Test", host="1.2.3.4", port=80,
        status=HostStatusEnum.UP, latency_ms=600.0,
    )
    alert = await engine.evaluate(host)
    assert alert is not None
    assert alert.severity == AlertSeverity.CRITICAL


@pytest.mark.asyncio
async def test_critical_on_consecutive_failures(engine, state):
    host = HostStatus(
        id="h2", name="Down Host", host="10.0.0.1", port=80,
        status=HostStatusEnum.DOWN, failure_count=3,
    )
    alert = await engine.evaluate(host)
    assert alert is not None
    assert alert.severity == AlertSeverity.CRITICAL
    assert "DOWN" in alert.message


@pytest.mark.asyncio
async def test_no_duplicate_alert_same_streak(engine, state):
    host = HostStatus(
        id="h3", name="Down", host="10.0.0.2", port=80,
        status=HostStatusEnum.DOWN, failure_count=3,
    )
    a1 = await engine.evaluate(host)
    assert a1 is not None

    # Same failure count — should NOT fire again
    a2 = await engine.evaluate(host)
    assert a2 is None


@pytest.mark.asyncio
async def test_streak_reset_on_recovery(engine, state):
    host_down = HostStatus(
        id="h4", name="Flappy", host="10.0.0.3", port=80,
        status=HostStatusEnum.DOWN, failure_count=3,
    )
    await engine.evaluate(host_down)

    # Host comes back up
    host_up = HostStatus(
        id="h4", name="Flappy", host="10.0.0.3", port=80,
        status=HostStatusEnum.UP, latency_ms=10.0, failure_count=0,
    )
    await engine.evaluate(host_up)

    # Goes down again — should alert again
    host_down2 = HostStatus(
        id="h4", name="Flappy", host="10.0.0.3", port=80,
        status=HostStatusEnum.DOWN, failure_count=3,
    )
    a = await engine.evaluate(host_down2)
    assert a is not None
