"""
Pydantic models for the Network Monitoring & Automation System.

Covers host configuration, runtime status, alerts, metrics, and API payloads.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class HostStatusEnum(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


class AlertSeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ── Configuration Models ─────────────────────────────────────────────────────

class HostConfig(BaseModel):
    """Defines a single host to monitor."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    host: str
    port: int = 80
    enabled: bool = True


class MonitoringConfig(BaseModel):
    check_interval: int = 30
    timeout: int = 5
    max_latency_history: int = 100


class AlertConfig(BaseModel):
    latency_warning_ms: float = 500.0
    latency_critical_ms: float = 2000.0
    consecutive_failures: int = 3
    retry_attempts: int = 2
    backoff_base: float = 1.0
    backoff_max: float = 30.0


class SlackConfig(BaseModel):
    enabled: bool = False
    webhook_url: str = ""


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    directory: str = "logs"


class AppConfig(BaseModel):
    monitoring: MonitoringConfig = MonitoringConfig()
    alerts: AlertConfig = AlertConfig()
    slack: SlackConfig = SlackConfig()
    hosts: list[HostConfig] = []
    logging: LoggingConfig = LoggingConfig()


# ── Runtime Models ───────────────────────────────────────────────────────────

class TCPHandshakeLog(BaseModel):
    """Captures one simulated TCP handshake attempt."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    host: str
    port: int
    step: str          # SYN | SYN-ACK | ACK | FAIL
    elapsed_ms: float
    message: str


class HostStatus(BaseModel):
    """Live health snapshot for a single monitored host."""
    id: str
    name: str
    host: str
    port: int
    status: HostStatusEnum = HostStatusEnum.UNKNOWN
    latency_ms: Optional[float] = None
    failure_count: int = 0
    last_checked: Optional[datetime] = None
    health_score: float = 100.0         # 0-100 %
    latency_history: list[float] = Field(default_factory=list)
    handshake_logs: list[TCPHandshakeLog] = Field(default_factory=list)


class Alert(BaseModel):
    """A single alert event."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    host_id: str
    host_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False


# ── API Payloads ─────────────────────────────────────────────────────────────

class AddHostRequest(BaseModel):
    name: str
    host: str
    port: int = 80


class HealthMetrics(BaseModel):
    """Aggregate dashboard metrics."""
    total_hosts: int = 0
    hosts_up: int = 0
    hosts_down: int = 0
    hosts_unknown: int = 0
    average_latency_ms: Optional[float] = None
    uptime_percentage: float = 100.0
    last_updated: Optional[datetime] = None
