# Task: T-A016 — Correlation ID middleware for Reminder Service
# Spec: NFR-026, Spec S8.3 (correlation_id in event envelope)
# Plan: S7.4 (Correlation ID Propagation)

import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_HEADER = "X-Correlation-ID"
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Generate or propagate X-Correlation-ID on every request.

    Plan S7.4: Generated at ingress if not present, passed through all
    Dapr service invocations, included in all Kafka event envelopes.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        cid = request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))
        correlation_id_var.set(cid)
        response = await call_next(request)
        response.headers[CORRELATION_HEADER] = cid
        return response


def get_correlation_id() -> str:
    return correlation_id_var.get() or str(uuid.uuid4())
