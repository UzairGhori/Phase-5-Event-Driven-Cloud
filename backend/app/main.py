# Task: T-A001 (prerequisite — FastAPI application entry point)
# Spec: §6 (Technology Stack), §11 (API Endpoints)
# Plan: §2.1 (Task API Service)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import create_db_and_tables
from backend.app.middleware.correlation import CorrelationMiddleware
from backend.app.middleware.logging import RequestLoggingMiddleware, setup_json_logging
from backend.app.middleware.metrics import MetricsMiddleware, metrics_router
from backend.app.routers import auth, health, tags, tasks
from backend.app.tracing import setup_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure logging, create tables (dev only)."""
    setup_json_logging(service_name=settings.SERVICE_NAME)
    setup_tracing(settings.SERVICE_NAME, app)
    create_db_and_tables()
    yield


app = FastAPI(
    title="Todo Task API",
    description="Phase V — Event-Driven Cloud Todo API",
    version="5.0.0",
    lifespan=lifespan,
)

# --- Middleware (order matters: outermost first) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# --- Routers ---
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(tags.router)
app.include_router(health.router)
app.include_router(metrics_router)
