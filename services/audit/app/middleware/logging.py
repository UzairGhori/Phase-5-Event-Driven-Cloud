# Task: T-A020 — Structured JSON logging middleware for Audit Service
# Spec: NFR-026
# Plan: S7.4 (Structured Logging -- JSON format)

import json
import logging
import sys
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.correlation import get_correlation_id


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter. Plan S7.4."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": getattr(record, "service", "audit-service"),
            "correlation_id": get_correlation_id(),
            "message": record.getMessage(),
        }
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "data"):
            log_entry["data"] = record.data
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_json_logging(service_name: str = "audit-service"):
    """Configure root logger with JSON formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with method, path, status, duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger = logging.getLogger("http")
        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
