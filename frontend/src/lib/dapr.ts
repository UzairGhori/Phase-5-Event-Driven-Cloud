// T-A027 — Dapr service invocation helper (server-side only)
// In K8s: calls via Dapr sidecar. In dev: calls FastAPI directly.

const DAPR_HTTP_PORT = process.env.DAPR_HTTP_PORT;
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const CHAT_URL = process.env.CHAT_API_URL || "http://localhost:8001";

export function taskApiUrl(path: string): string {
  if (DAPR_HTTP_PORT) {
    return `http://localhost:${DAPR_HTTP_PORT}/v1.0/invoke/task-api/method${path}`;
  }
  return `${BACKEND_URL}${path}`;
}

export function chatApiUrl(path: string): string {
  if (DAPR_HTTP_PORT) {
    return `http://localhost:${DAPR_HTTP_PORT}/v1.0/invoke/chat-api/method${path}`;
  }
  return `${CHAT_URL}${path}`;
}

export function forwardHeaders(req: Request): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  const auth = req.headers.get("Authorization");
  if (auth) headers["Authorization"] = auth;
  const corr = req.headers.get("X-Correlation-ID");
  if (corr) headers["X-Correlation-ID"] = corr;
  return headers;
}
