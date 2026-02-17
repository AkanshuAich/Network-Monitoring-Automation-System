"""Tests for TCP Analyzer."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from tcp_analyzer import tcp_check, TCPCheckResult


@pytest.mark.asyncio
async def test_tcp_check_success():
    """Successful TCP connection returns success=True with latency."""
    mock_writer = AsyncMock()
    mock_writer.close = lambda: None
    mock_writer.wait_closed = AsyncMock()

    with patch("tcp_analyzer.asyncio.open_connection", return_value=(AsyncMock(), mock_writer)):
        result = await tcp_check("127.0.0.1", 80, timeout=2.0)

    assert result.success is True
    assert result.latency_ms >= 0
    assert result.error is None
    assert result.handshake_logs is not None
    assert len(result.handshake_logs) == 3  # SYN, SYN-ACK, ACK


@pytest.mark.asyncio
async def test_tcp_check_timeout():
    """Timeout produces failure result."""
    with patch(
        "tcp_analyzer.asyncio.open_connection",
        side_effect=asyncio.TimeoutError(),
    ):
        result = await tcp_check("192.0.2.1", 80, timeout=0.1)

    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_tcp_check_connection_refused():
    """Connection refused produces failure result."""
    with patch(
        "tcp_analyzer.asyncio.open_connection",
        side_effect=ConnectionRefusedError("refused"),
    ):
        result = await tcp_check("127.0.0.1", 9999, timeout=1.0)

    assert result.success is False
    assert "refused" in (result.error or "")


@pytest.mark.asyncio
async def test_tcp_check_no_debug():
    """With debug_handshake=False, no handshake logs are emitted."""
    mock_writer = AsyncMock()
    mock_writer.close = lambda: None
    mock_writer.wait_closed = AsyncMock()

    with patch("tcp_analyzer.asyncio.open_connection", return_value=(AsyncMock(), mock_writer)):
        result = await tcp_check("127.0.0.1", 80, debug_handshake=False)

    assert result.success is True
    assert result.handshake_logs == []
