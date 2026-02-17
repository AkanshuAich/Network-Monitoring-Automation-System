"""Tests for FastAPI REST endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_list_hosts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/hosts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_hosts" in data
    assert "average_latency_ms" in data


@pytest.mark.asyncio
async def test_get_alerts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_add_host():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/hosts", json={
            "name": "Test Host",
            "host": "192.168.1.1",
            "port": 8080,
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Host"
    assert data["port"] == 8080


@pytest.mark.asyncio
async def test_get_host_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/hosts/nonexistent")
    assert resp.status_code == 404
