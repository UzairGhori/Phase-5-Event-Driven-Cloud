# Task: T-A025, T-A026 — Dapr Service Invocation helper for Chat API
# Plan: §2.2, §4.2

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

DAPR_BASE_URL = f"http://localhost:{settings.DAPR_HTTP_PORT}"


async def invoke_task_api(
    method: str,
    data: dict[str, Any] | None = None,
    http_method: str = "GET",
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Invoke Task API method via Dapr Service Invocation."""
    url = f"{DAPR_BASE_URL}/v1.0/invoke/{settings.TASK_API_APP_ID}/method/{method}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if http_method == "POST":
                resp = await client.post(url, json=data, headers=req_headers, params=params)
            elif http_method == "PATCH":
                resp = await client.patch(url, json=data, headers=req_headers, params=params)
            elif http_method == "DELETE":
                resp = await client.delete(url, headers=req_headers, params=params)
            else:
                resp = await client.get(url, headers=req_headers, params=params)

            if resp.status_code in (200, 201, 204):
                if resp.status_code == 204:
                    return {"status": "ok"}
                return resp.json()
            logger.warning("Task API %s %s returned %d", http_method, method, resp.status_code)
            return None
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Task API invocation failed: %s", str(exc))
        return None
