// T-A031 — WebSocket client with exponential backoff reconnect

import { WsEvent } from "@/types";

type Listener = (event: WsEvent) => void;

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080/ws";

export class WsClient {
  private ws: WebSocket | null = null;
  private listeners: Listener[] = [];
  private retryMs = 1000;
  private token: string;
  private closed = false;

  constructor(token: string) {
    this.token = token;
  }

  connect() {
    this.closed = false;
    this.ws = new WebSocket(`${WS_URL}?token=${this.token}`);
    this.ws.onmessage = (e) => {
      try {
        const ev: WsEvent = JSON.parse(e.data);
        this.listeners.forEach((fn) => fn(ev));
      } catch { /* ignore parse errors */ }
    };
    this.ws.onclose = () => {
      if (!this.closed) this.reconnect();
    };
    this.ws.onerror = () => this.ws?.close();
  }

  private reconnect() {
    setTimeout(() => {
      this.connect();
      this.retryMs = Math.min(this.retryMs * 2, 30000);
    }, this.retryMs);
  }

  onEvent(fn: Listener) {
    this.listeners.push(fn);
  }

  close() {
    this.closed = true;
    this.ws?.close();
  }
}
