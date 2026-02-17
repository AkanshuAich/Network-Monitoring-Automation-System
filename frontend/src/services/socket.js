/**
 * WebSocket service — manages a persistent connection to /ws/health
 * with automatic reconnect and exponential backoff.
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/health';

class SocketService {
    constructor() {
        this.ws = null;
        this.listeners = new Set();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 20;
        this.reconnectTimer = null;
        this.intentionallyClosed = false;
    }

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.intentionallyClosed = false;

        try {
            this.ws = new WebSocket(WS_URL);

            this.ws.onopen = () => {
                console.log('[WS] Connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.listeners.forEach((fn) => fn(data));
                } catch (err) {
                    console.error('[WS] Bad message:', err);
                }
            };

            this.ws.onerror = (err) => {
                console.error('[WS] Error:', err);
            };

            this.ws.onclose = () => {
                console.log('[WS] Disconnected');
                if (!this.intentionallyClosed) {
                    this._scheduleReconnect();
                }
            };
        } catch (err) {
            console.error('[WS] Connection failed:', err);
            this._scheduleReconnect();
        }
    }

    disconnect() {
        this.intentionallyClosed = true;
        clearTimeout(this.reconnectTimer);
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    subscribe(fn) {
        this.listeners.add(fn);
        return () => this.listeners.delete(fn);
    }

    _scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('[WS] Max reconnect attempts reached');
            return;
        }
        const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
        this.reconnectAttempts++;
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        this.reconnectTimer = setTimeout(() => this.connect(), delay);
    }
}

const socketService = new SocketService();
export default socketService;
