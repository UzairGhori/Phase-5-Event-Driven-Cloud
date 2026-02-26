# Task: T-A013 — Recurring Task Service FastAPI app
# Spec: §7.2, FR-031
# Plan: §1.1 (Service #4), §2.4

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.handlers.task_completed import router as task_completed_router
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.logging import RequestLoggingMiddleware, setup_json_logging
from app.middleware.metrics import MetricsMiddleware, metrics_router
from app.routers.health import router as health_router
from app.tracing import setup_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_json_logging(service_name=settings.SERVICE_NAME)
    setup_tracing(settings.SERVICE_NAME, app)
    yield


app = FastAPI(
    title="Recurring Task Service",
    description="Generates next task instances on completion events",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(task_completed_router)
app.include_router(metrics_router)
