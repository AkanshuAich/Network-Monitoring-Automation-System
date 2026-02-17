"""
TCP Analyzer — Asynchronous TCP connection checker with handshake simulation.

Performs real TCP connection checks while logging a simulated
SYN → SYN-ACK → ACK handshake sequence for educational / debug purposes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from models import TCPHandshakeLog

logger = logging.getLogger("tcp_analyzer")


@dataclass
class TCPCheckResult:
    """Result of a single TCP probe."""
    success: bool
    latency_ms: float
    error: Optional[str] = None
    handshake_logs: list[TCPHandshakeLog] | None = None


async def tcp_check(
    host: str,
    port: int,
    timeout: float = 5.0,
    debug_handshake: bool = True,
) -> TCPCheckResult:
    """
    Open a TCP connection to *host*:*port* and measure round-trip latency.

    When *debug_handshake* is ``True`` the function emits simulated
    SYN → SYN-ACK → ACK log entries so users can study the three-way
    handshake flow.
    """
    logs: list[TCPHandshakeLog] = []
    start = time.perf_counter()

    try:
        # ── Step 1: SYN (client → server) ────────────────────────────
        if debug_handshake:
            syn_log = TCPHandshakeLog(
                host=host,
                port=port,
                step="SYN",
                elapsed_ms=0.0,
                message=f"[SYN] Initiating TCP connection to {host}:{port}",
            )
            logs.append(syn_log)
            logger.debug("SYN → %s:%s", host, port)

        # Actual async TCP connect
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # ── Step 2: SYN-ACK (server → client) ───────────────────────
        if debug_handshake:
            synack_log = TCPHandshakeLog(
                host=host,
                port=port,
                step="SYN-ACK",
                elapsed_ms=elapsed_ms * 0.6,   # approximate split
                message=f"[SYN-ACK] Received acknowledgement from {host}:{port}",
            )
            logs.append(synack_log)
            logger.debug("SYN-ACK ← %s:%s (%.2f ms)", host, port, elapsed_ms * 0.6)

        # ── Step 3: ACK (client → server) ────────────────────────────
        if debug_handshake:
            ack_log = TCPHandshakeLog(
                host=host,
                port=port,
                step="ACK",
                elapsed_ms=elapsed_ms,
                message=f"[ACK] Connection established with {host}:{port} in {elapsed_ms:.2f} ms",
            )
            logs.append(ack_log)
            logger.debug("ACK → %s:%s — connection established (%.2f ms)", host, port, elapsed_ms)

        # Clean close
        writer.close()
        await writer.wait_closed()

        return TCPCheckResult(
            success=True,
            latency_ms=round(elapsed_ms, 2),
            handshake_logs=logs,
        )

    except (asyncio.TimeoutError, OSError, ConnectionRefusedError) as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000

        if debug_handshake:
            fail_log = TCPHandshakeLog(
                host=host,
                port=port,
                step="FAIL",
                elapsed_ms=elapsed_ms,
                message=f"[FAIL] Connection to {host}:{port} failed — {exc!r}",
            )
            logs.append(fail_log)

        logger.warning("TCP check failed for %s:%s — %s", host, port, exc)

        return TCPCheckResult(
            success=False,
            latency_ms=round(elapsed_ms, 2),
            error=str(exc),
            handshake_logs=logs,
        )
