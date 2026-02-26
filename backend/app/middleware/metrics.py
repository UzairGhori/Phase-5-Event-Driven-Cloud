# Task: T-G002 — Prometheus metrics middleware
# Spec: NFR-027
# Plan: §7.1 (Custom Application Metrics)

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter

SERVICE_LABEL = "task-api"

# --- Plan §7.1: All 10 custom application metrics ---

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

kafka_events_published = Counter(
    "kafka_events_published_total",
    "Events published to Kafka",
    ["topic", "service"],
)

kafka_events_consumed = Counter(
    "kafka_events_consumed_total",
    "Events consumed from Kafka",
    ["topic", "consumer_group", "service"],
)

kafka_events_failed = Counter(
    "kafka_events_failed_total",
    "Failed event processing",
    ["topic", "consumer_group", "service"],
)

active_websocket_connections = Gauge(
    "active_websocket_connections",
    "Current WebSocket connections",
    ["service"],
)

dapr_job_scheduled_total = Counter(
    "dapr_job_scheduled_total",
    "Dapr Jobs scheduled",
    ["service"],
)

dapr_job_triggered_total = Counter(
    "dapr_job_triggered_total",
    "Dapr Jobs fired",
    ["service"],
)

tasks_created_total = Counter(
    "tasks_created_total",
    "Tasks created",
    ["service"],
)

tasks_completed_total = Counter(
    "tasks_completed_total",
    "Tasks completed",
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
    """Prometheus scrape endpoint. Plan §7.1."""
    from starlette.responses import Response as StarletteResponse
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
