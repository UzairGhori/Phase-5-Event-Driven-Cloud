# Task: T-A025 — Chat API Service FastAPI app
# Spec: FR-046, FR-047
# Plan: §1.1 (Service #2), §2.2

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.logging import RequestLoggingMiddleware, setup_json_logging
from app.middleware.metrics import MetricsMiddleware, metrics_router
from app.routers.chat import router as chat_router
from app.routers.health import router as health_router
from app.tracing import setup_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_json_logging(service_name=settings.SERVICE_NAME)
    setup_tracing(settings.SERVICE_NAME, app)
    yield


app = FastAPI(
    title="Chat API Service",
    description="AI-powered task assistant with MCP tools",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(metrics_router)
