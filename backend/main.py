"""
Network Monitoring & Automation System — FastAPI Application.

Exposes REST endpoints and a WebSocket for real-time health dashboards.
Bootstraps the async monitoring engine on startup and tears it down
gracefully on shutdown.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from alert_engine import AlertEngine
from dashboard_state import DashboardState
from models import (
    AddHostRequest,
    Alert,
    AlertSeverity,
    AppConfig,
    HealthMetrics,
    HostConfig,
    HostStatus,
)
from monitor import MonitorEngine

# ── Logging Setup ────────────────────────────────────────────────────────────

def _setup_logging(cfg: dict) -> None:
    log_dir = Path(cfg.get("directory", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, cfg.get("level", "INFO").upper(), logging.INFO)
    use_json = cfg.get("format", "json") == "json"

    if use_json:
        fmt = json.dumps({
            "time": "%(asctime)s",
            "level": "%(levelname)s",
            "logger": "%(name)s",
            "message": "%(message)s",
        })
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "monitor.log", encoding="utf-8"),
    ]

    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


# ── Config Loader ────────────────────────────────────────────────────────────

def _load_config() -> AppConfig:
    config_path = Path(os.getenv("CONFIG_PATH", "config.yaml"))
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = {}

    # Override Slack webhook from env
    slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if slack_url:
        raw.setdefault("slack", {})["webhook_url"] = slack_url
        raw["slack"]["enabled"] = True

    return AppConfig(**raw)


# ── Shared State (module-level singletons) ───────────────────────────────────

config = _load_config()
_setup_logging(config.logging.model_dump())

state = DashboardState(max_latency_history=config.monitoring.max_latency_history)
alert_engine = AlertEngine(state=state, config=config.alerts, slack=config.slack)
monitor = MonitorEngine(config=config, state=state, alert_engine=alert_engine)

logger = logging.getLogger("main")


# ── FastAPI Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting monitoring engine …")
    await monitor.start()
    yield
    logger.info("Shutting down monitoring engine …")
    await monitor.stop()


app = FastAPI(
    title="Network Monitor API",
    version="1.0.0",
    description="Real-time network monitoring & automation system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/hosts", response_model=list[HostStatus], tags=["Hosts"])
async def list_hosts():
    """Return the current status of every monitored host."""
    return await state.get_all_hosts()


@app.get("/hosts/{host_id}", response_model=HostStatus, tags=["Hosts"])
async def get_host(host_id: str):
    """Return detailed status for a single host."""
    host = await state.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@app.post("/hosts", response_model=HostStatus, status_code=201, tags=["Hosts"])
async def add_host(req: AddHostRequest):
    """Add a new host to the monitoring pool."""
    hc = HostConfig(name=req.name, host=req.host, port=req.port)
    await monitor.add_host(hc)
    host = await state.get_host(hc.id)
    return host


@app.get("/alerts", response_model=list[Alert], tags=["Alerts"])
async def list_alerts(severity: Optional[AlertSeverity] = Query(None)):
    """Return triggered alerts, optionally filtered by severity."""
    return await state.get_alerts(severity=severity)


@app.get("/metrics", response_model=HealthMetrics, tags=["Metrics"])
async def get_metrics():
    """Aggregate health metrics across all hosts."""
    return await state.get_metrics()


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/health")
async def ws_health(websocket: WebSocket):
    """Push real-time host-status updates to the connected client."""
    await websocket.accept()
    queue = state.subscribe()
    logger.info("WebSocket client connected")
    try:
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
    finally:
        state.unsubscribe(queue)
