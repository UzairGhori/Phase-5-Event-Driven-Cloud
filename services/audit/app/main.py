# Task: T-A020 — Audit Service FastAPI app
# Spec: §10.4, FR-044
# Plan: §1.1 (Service #5), §2.5

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.handlers.audit_log import router as audit_log_router
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.logging import RequestLoggingMiddleware, setup_json_logging
from app.middleware.metrics import MetricsMiddleware, metrics_router
from app.routers.audit import router as audit_query_router
from app.routers.health import router as health_router
from app.tracing import setup_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_json_logging(service_name=settings.SERVICE_NAME)
    setup_tracing(settings.SERVICE_NAME, app)
    yield


app = FastAPI(
    title="Audit Service",
    description="Persists and queries domain event audit trail",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(audit_log_router)
app.include_router(audit_query_router)
app.include_router(metrics_router)
