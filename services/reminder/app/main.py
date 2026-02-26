# Task: T-A016 — Reminder Service FastAPI app
# Spec: §7.2, FR-029
# Plan: §1.1 (Service #3), §2.3

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.handlers.reminder_scheduled import router as reminder_scheduled_router
from app.handlers.task_deleted import router as task_deleted_router
from app.handlers.task_updated import router as task_updated_router
from app.jobs.reminder_triggered import router as jobs_router
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
    title="Reminder Service",
    description="Schedules and triggers task reminders via Dapr Jobs API",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(reminder_scheduled_router)
app.include_router(task_deleted_router)
app.include_router(task_updated_router)
app.include_router(jobs_router)
app.include_router(metrics_router)
