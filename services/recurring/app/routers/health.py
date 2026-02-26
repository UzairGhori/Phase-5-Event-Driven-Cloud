# Task: T-A013 — Recurring Service health probes
# Spec: §11.3, FR-045

import httpx
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])
settings = get_settings()


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.get("/ready")
def readiness():
    checks = {}
    try:
        resp = httpx.get(
            f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/healthz",
            timeout=2.0,
        )
        checks["dapr"] = "available" if resp.status_code == 204 else "unavailable"
    except Exception:
        checks["dapr"] = "unavailable"

    all_ok = all(v in ("connected", "available") for v in checks.values())
    status = "ready" if all_ok else "degraded"
    status_code = 200 if all_ok else 503

    from starlette.responses import JSONResponse
    return JSONResponse(content={"status": status, "checks": checks}, status_code=status_code)
