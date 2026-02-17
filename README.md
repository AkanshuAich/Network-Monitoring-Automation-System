# 🖥️ Network Monitoring & Automation System

A production-ready, full-stack network monitoring platform inspired by **Datadog** and **Pingdom**. Monitors host health via asynchronous TCP probes, tracks latency and uptime, fires threshold-based alerts, and streams live updates to a slick React dashboard.

---

## 📐 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│   Dashboard  ·  Host Detail  ·  Alerts                       │
│       ↕ REST (Axios)           ↕ WebSocket                   │
└──────────────────────┬────────────────┬──────────────────────┘
                       │                │
                       ▼                ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI  (Uvicorn)                          │
│                                                              │
│   GET /hosts · GET /hosts/{id} · POST /hosts                 │
│   GET /alerts · GET /metrics · WS /ws/health                 │
└────────┬─────────────┬───────────────┬───────────────────────┘
         │             │               │
         ▼             ▼               ▼
  ┌────────────┐ ┌───────────┐ ┌──────────────┐
  │  Monitor   │ │ Dashboard │ │    Alert      │
  │  Engine    │ │   State   │ │   Engine      │
  │ (asyncio)  │ │ (in-mem)  │ │ (thresholds)  │
  └─────┬──────┘ └───────────┘ └──────┬───────┘
        │                              │
        ▼                              ▼
  ┌────────────┐                ┌─────────────┐
  │    TCP     │                │    Slack     │
  │  Analyzer  │                │  Webhook    │
  └────────────┘                └─────────────┘
```

| Layer            | Technology                         |
|------------------|------------------------------------|
| Frontend         | React 18, Vite 5, TailwindCSS 3    |
| Charts           | Recharts                           |
| HTTP Client      | Axios                              |
| API Framework    | FastAPI + Uvicorn                  |
| Async Runtime    | Python 3.11 asyncio                |
| Data Models      | Pydantic v2                        |
| Containerisation | Docker + Docker Compose            |

---

## 🔌 TCP Three-Way Handshake

Every host probe performs a real TCP connection and **logs a simulated handshake** for educational / debug purposes:

```
Client                    Server
  │                         │
  │ ──── SYN ──────────►    │   Step 1: Client sends SYN
  │                         │
  │ ◄─── SYN-ACK ──────    │   Step 2: Server acknowledges
  │                         │
  │ ──── ACK ──────────►    │   Step 3: Connection established
  │                         │
  │ ◄──► DATA ◄──────►     │   Application data flows
  │                         │
  │ ──── FIN ──────────►    │   Graceful close
```

The system measures total round-trip time (SYN → ACK) to produce a **latency** reading in milliseconds. Debug logs show the timing of each simulated step inside `tcp_analyzer.py`.

---

## ⚡ Concurrency Model

```
                     ┌─────────  asyncio event loop  ─────────┐
                     │                                         │
  check_host(A) ─────┤                                         │
  check_host(B) ─────┤   asyncio.gather (fan-out)              │
  check_host(C) ─────┤                                         │
  check_host(D) ─────┤                                         │
                     │         ▼                               │
                     │   asyncio.open_connection(host, port)   │
                     │         │                               │
                     │   non-blocking I/O — no threads         │
                     └─────────────────────────────────────────┘
```

* **Single-threaded, non-blocking**: All probes run on one asyncio event loop.
* **Fan-out**: Every check cycle fires `asyncio.gather` across all hosts concurrently.
* **No GIL bottleneck**: Pure I/O-bound work — `asyncio.open_connection` suspends at the OS `epoll` / `IOCP` level.
* **Graceful shutdown**: An `asyncio.Event` signals the loop to stop; in-flight probes finish before exit.

---

## 📈 Scaling to 10 000+ Hosts

| Concern | Strategy |
|---------|----------|
| **Connection concurrency** | `asyncio.Semaphore` to cap open file descriptors (e.g. 500 concurrent). |
| **Check interval** | Stagger hosts into batches; each batch runs on a timer offset. |
| **State storage** | Migrate from in-memory dict to **Redis** or **TimescaleDB** for persistence and horizontal scaling. |
| **API throughput** | Run multiple Uvicorn workers behind **nginx**; shard WebSocket rooms by host group. |
| **Alerting** | Decouple via **message queue** (RabbitMQ / Kafka) so the alert engine scales independently. |
| **Deployment** | Kubernetes `Deployment` with `HPA` on CPU/memory; one pod per N hosts. |

---

## 🔁 Retry & Back-off Strategy

```
attempt 1  →  fail  →  wait  1 s
attempt 2  →  fail  →  wait  2 s
attempt 3  →  fail  →  wait  4 s  (capped at backoff_max)
final      →  fail  →  mark DOWN, fire alert
```

Configured in `config.yaml`:

```yaml
alerts:
  retry_attempts: 2       # retries before giving up
  backoff_base: 1.0       # initial wait (seconds)
  backoff_max: 30.0       # ceiling
  consecutive_failures: 3 # trigger CRITICAL after N consecutive failures
```

---

## 🚀 Quick Start

### Prerequisites
* Python 3.11+
* Node.js 18+
* (Optional) Docker & Docker Compose

### Backend

```bash
cd backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://localhost:8000/docs** for Swagger UI.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**.

---

## 🐳 Docker

```bash
# Build & run both services
docker-compose up --build

# Backend → http://localhost:8000
# Frontend → http://localhost:3000
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | `config.yaml` | Path to YAML config |
| `SLACK_WEBHOOK_URL` | _(empty)_ | Slack incoming webhook URL |

---

## 🐧 Linux Deployment

1. Copy the project to `/opt/netmonitor`.
2. Create a virtualenv and install deps.
3. Install the systemd unit:

```bash
sudo cp netmonitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now netmonitor
```

4. Serve the frontend build via Nginx (`frontend/Dockerfile` contains a reference config).

---

## 🧪 Running Tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## 📁 Project Structure

```
Network-Monitoring-Automation-System/
├── backend/
│   ├── main.py              # FastAPI app, REST + WebSocket
│   ├── monitor.py           # Async monitoring engine
│   ├── tcp_analyzer.py      # TCP probe + handshake simulation
│   ├── dashboard_state.py   # In-memory health store
│   ├── alert_engine.py      # Threshold alerts + Slack
│   ├── models.py            # Pydantic models
│   ├── config.yaml          # Default configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       ├── test_models.py
│       ├── test_tcp_analyzer.py
│       ├── test_alert_engine.py
│       └── test_api.py
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, HostCard, StatusBadge, …
│   │   ├── pages/           # Dashboard, HostDetail, Alerts
│   │   ├── services/        # api.js, socket.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── netmonitor.service        # systemd unit
└── README.md
```

---

## 🎤 Interview Talking Points

1. **Why asyncio over threading?** — Network monitoring is I/O-bound; asyncio gives thousands of concurrent connections on a single thread without GIL contention or context-switch overhead.

2. **Health Score Design** — Weighted composite (60 % uptime, 25 % latency, 15 % failure recency) gives a single glanceable metric without masking individual signals.

3. **Alert Deduplication** — We track the last-alerted failure streak per host to avoid alert storms while still re-firing after recovery + re-failure.

4. **WebSocket Fan-out** — A simple in-process pub/sub (`asyncio.Queue` per client) keeps the architecture lightweight; for >1 000 clients, swap for Redis Pub/Sub or a message broker.

5. **Exponential Back-off** — Prevents flood-checking a host that's already overloaded, bounded by `backoff_max` to avoid infinite delays.

6. **Containerisation** — Multi-stage Docker builds keep images small (<100 MB frontend, ~150 MB backend). Docker Compose wires both services with a single command.

7. **Scaling Path** — The architecture separates concerns (monitor ↔ state ↔ alerting) so each can scale independently via Kubernetes or serverless workers.

---

## 📄 License

MIT — use freely for learning, interviews, or production.
