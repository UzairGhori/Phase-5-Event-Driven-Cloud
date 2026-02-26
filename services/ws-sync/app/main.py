# Task: T-A023 — WebSocket Sync Service FastAPI app
# Plan: §1.1 (Service #6), §2.6

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.handlers.reminder_events import router as reminder_events_router
from app.handlers.task_events import router as task_events_router
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.logging import RequestLoggingMiddleware, setup_json_logging
from app.middleware.metrics import MetricsMiddleware, metrics_router
from app.routers.health import router as health_router
from app.tracing import setup_tracing
from app.routers.ws import router as ws_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_json_logging(service_name=settings.SERVICE_NAME)
    setup_tracing(settings.SERVICE_NAME, app)
    yield


app = FastAPI(
    title="WebSocket Sync Service",
    description="Real-time task event push via WebSocket",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(ws_router)
app.include_router(task_events_router)
app.include_router(reminder_events_router)
app.include_router(metrics_router)
