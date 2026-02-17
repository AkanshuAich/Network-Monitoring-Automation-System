"""Tests for Pydantic models."""

from models import (
    AddHostRequest,
    Alert,
    AlertSeverity,
    AppConfig,
    HealthMetrics,
    HostConfig,
    HostStatus,
    HostStatusEnum,
    TCPHandshakeLog,
)


class TestHostConfig:
    def test_defaults(self):
        hc = HostConfig(name="Test", host="1.2.3.4")
        assert hc.port == 80
        assert hc.enabled is True
        assert len(hc.id) == 8

    def test_custom_port(self):
        hc = HostConfig(name="Test", host="example.com", port=443)
        assert hc.port == 443


class TestHostStatus:
    def test_defaults(self):
        hs = HostStatus(id="abc", name="Test", host="1.2.3.4", port=80)
        assert hs.status == HostStatusEnum.UNKNOWN
        assert hs.failure_count == 0
        assert hs.health_score == 100.0
        assert hs.latency_history == []


class TestAlert:
    def test_creation(self):
        a = Alert(
            host_id="abc",
            host_name="Test",
            severity=AlertSeverity.WARNING,
            message="High latency",
        )
        assert a.resolved is False
        assert len(a.id) == 8
        assert a.severity == AlertSeverity.WARNING


class TestHealthMetrics:
    def test_defaults(self):
        m = HealthMetrics()
        assert m.total_hosts == 0
        assert m.uptime_percentage == 100.0


class TestAddHostRequest:
    def test_required_fields(self):
        req = AddHostRequest(name="Google", host="8.8.8.8", port=53)
        assert req.name == "Google"


class TestAppConfig:
    def test_from_dict(self):
        cfg = AppConfig(
            hosts=[{"name": "Test", "host": "1.2.3.4", "port": 80}],
        )
        assert len(cfg.hosts) == 1
        assert cfg.monitoring.check_interval == 30
