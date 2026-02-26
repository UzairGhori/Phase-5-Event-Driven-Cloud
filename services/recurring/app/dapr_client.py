# Task: T-A015 — Dapr Service Invocation helper for Recurring Service
# Spec: §9.1 (Dapr Service Invocation)
# Plan: §4.2 (Service-to-Service via Dapr)

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

DAPR_BASE_URL = f"http://localhost:{settings.DAPR_HTTP_PORT}"


async def invoke_service(
    app_id: str,
    method: str,
    data: dict[str, Any],
    http_method: str = "POST",
    headers: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Invoke a Dapr service method via HTTP API.

    Plan §4.2: All inter-service calls go through Dapr sidecar.
    """
    url = f"{DAPR_BASE_URL}/v1.0/invoke/{app_id}/method/{method}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if http_method == "POST":
                response = await client.post(url, json=data, headers=req_headers)
            elif http_method == "GET":
                response = await client.get(url, headers=req_headers)
            else:
                response = await client.request(http_method, url, json=data, headers=req_headers)

            if response.status_code in (200, 201):
                return response.json()
            logger.warning(
                "Dapr invoke %s/%s returned %d: %s",
                app_id, method, response.status_code, response.text,
            )
            return None
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Dapr invoke %s/%s failed: %s", app_id, method, str(exc))
        return None
