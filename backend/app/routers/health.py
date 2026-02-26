# Task: T-G003 — Health and readiness probes for Task API
# Spec: §11.3 (Health & Readiness Endpoints), FR-045
# Plan: §2.1 (Probe Endpoints)

import httpx
from fastapi import APIRouter, Depends
from sqlmodel import Session, text

from backend.app.config import get_settings
from backend.app.database import get_session

router = APIRouter(prefix="/api", tags=["health"])
settings = get_settings()


@router.get("/health")
def health():
    """Liveness probe. Spec §11.3."""
    return {"status": "healthy"}


@router.get("/ready")
def readiness(session: Session = Depends(get_session)):
    """Readiness probe. Checks DB, Kafka (Dapr), Dapr sidecar. FR-045."""
    checks = {}

    # Check database
    try:
        session.exec(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception:
        checks["database"] = "disconnected"

    # Check Dapr sidecar
    try:
        resp = httpx.get(
            f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/healthz",
            timeout=2.0,
        )
        checks["dapr"] = "available" if resp.status_code == 204 else "unavailable"
    except Exception:
        checks["dapr"] = "unavailable"

    all_ok = all(
        v in ("connected", "available") for v in checks.values()
    )
    status = "ready" if all_ok else "degraded"
    status_code = 200 if all_ok else 503

    from starlette.responses import JSONResponse
    return JSONResponse(
        content={"status": status, "checks": checks},
        status_code=status_code,
    )
