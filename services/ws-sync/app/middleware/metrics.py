# Task: T-A023 — Prometheus metrics middleware for WebSocket Sync Service
# Spec: NFR-027
# Plan: S7.1 (Custom Application Metrics)

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter

SERVICE_LABEL = "ws-sync-service"

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "service"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "service"],
)

kafka_events_consumed = Counter(
    "kafka_events_consumed_total",
    "Events consumed from Kafka",
    ["topic", "service"],
)

websocket_connections_active = Gauge(
    "websocket_connections_active",
    "Currently active WebSocket connections",
    ["service"],
)

websocket_messages_sent = Counter(
    "websocket_messages_sent_total",
    "WebSocket messages sent to clients",
    ["service"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track HTTP request count and latency per endpoint."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        endpoint = request.url.path
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code),
            service=SERVICE_LABEL,
        ).inc()
        http_request_duration.labels(
            method=request.method,
            endpoint=endpoint,
            service=SERVICE_LABEL,
        ).observe(duration)
        return response


metrics_router = APIRouter()


@metrics_router.get("/metrics")
async def metrics_endpoint():
    """Prometheus scrape endpoint. Plan S7.1."""
    from starlette.responses import Response as StarletteResponse
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
