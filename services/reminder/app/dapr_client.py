# Task: T-A017 — Dapr Jobs API and Service Invocation helper for Reminder Service
# Spec: §9.3 (Dapr Jobs API), FR-029
# Plan: §4.5 (Dapr Jobs API Usage)

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
    data: dict[str, Any] | None = None,
    http_method: str = "GET",
    headers: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Invoke a Dapr service method. Plan §4.2."""
    url = f"{DAPR_BASE_URL}/v1.0/invoke/{app_id}/method/{method}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if http_method == "POST":
                response = await client.post(url, json=data, headers=req_headers)
            else:
                response = await client.get(url, headers=req_headers)

            if response.status_code in (200, 201):
                return response.json()
            logger.warning(
                "Dapr invoke %s/%s returned %d",
                app_id, method, response.status_code,
            )
            return None
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Dapr invoke %s/%s failed: %s", app_id, method, str(exc))
        return None


async def schedule_job(job_name: str, due_time: str, data: dict[str, Any]) -> bool:
    """Schedule a one-time Dapr Job. Plan §4.5.

    Args:
        job_name: Unique job identifier (e.g., "reminder-{task_id}")
        due_time: ISO 8601 datetime when the job should fire
        data: Payload delivered when job fires
    """
    url = f"{DAPR_BASE_URL}/v1.0-alpha1/jobs/{job_name}"
    payload = {
        "dueTime": due_time,
        "data": data,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.put(url, json=payload)
            if response.status_code in (200, 201, 204):
                logger.info("Scheduled job %s at %s", job_name, due_time)
                return True
            logger.warning(
                "Failed to schedule job %s: %d %s",
                job_name, response.status_code, response.text,
            )
            return False
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Dapr Jobs API error for %s: %s", job_name, str(exc))
        return False


async def cancel_job(job_name: str) -> bool:
    """Cancel a scheduled Dapr Job. Plan §4.5."""
    url = f"{DAPR_BASE_URL}/v1.0-alpha1/jobs/{job_name}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.delete(url)
            if response.status_code in (200, 204):
                logger.info("Cancelled job %s", job_name)
                return True
            if response.status_code == 404:
                logger.info("Job %s not found (already fired or never existed)", job_name)
                return True
            logger.warning("Failed to cancel job %s: %d", job_name, response.status_code)
            return False
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Dapr Jobs API cancel error for %s: %s", job_name, str(exc))
        return False
