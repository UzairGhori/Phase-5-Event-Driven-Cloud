# Task: T-A019 — Dapr Jobs callback (reminder triggered)
# Spec: §8.3, Edge Cases
# Plan: §3.4 Flow 3, §4.5

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Request

from app.config import get_settings
from app.dapr_client import invoke_service
from app.middleware.correlation import get_correlation_id

logger = logging.getLogger(__name__)
settings = get_settings()

DAPR_BASE_URL = f"http://localhost:{settings.DAPR_HTTP_PORT}"
PUBSUB_NAME = "pubsub-kafka"

router = APIRouter()


@router.post("/jobs/reminder-triggered")
async def handle_reminder_triggered(request: Request) -> dict[str, str]:
    """Dapr Jobs callback when a reminder fires.

    Plan §3.4 Flow 3:
    1. Dapr fires job callback
    2. Check task status via Service Invocation
    3. If not completed: publish reminder.triggered event
    4. If completed: log and discard
    """
    body = await request.json()
    task_id = body.get("task_id", "")
    user_id = body.get("user_id", "")
    task_title = body.get("task_title", "")

    if not task_id:
        logger.warning("Reminder triggered with no task_id")
        return {"status": "SKIP"}

    # Check task status via Dapr Service Invocation
    task = await invoke_service(
        app_id=settings.TASK_API_APP_ID,
        method=f"api/tasks/{task_id}",
        http_method="GET",
        headers={"X-User-ID": user_id},
    )

    if task and task.get("status") == "completed":
        logger.info("Task %s already completed, discarding reminder", task_id)
        return {"status": "DISCARDED"}

    # Publish reminder.triggered event via Dapr Pub/Sub
    now = datetime.now(timezone.utc).isoformat()
    event_payload = {
        "event_type": "reminder.triggered",
        "source": "reminder-service",
        "correlation_id": get_correlation_id(),
        "user_id": user_id,
        "data": {
            "task_id": task_id,
            "task_title": task_title,
            "triggered_at": now,
            "action": "log",
        },
    }

    url = f"{DAPR_BASE_URL}/v1.0/publish/{PUBSUB_NAME}/todo.reminder.triggered"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=event_payload)
            if resp.status_code in (200, 204):
                logger.info("Published reminder.triggered for task %s", task_id)
                return {"status": "OK"}
            logger.warning("Failed to publish reminder.triggered: %d", resp.status_code)
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Dapr publish failed for reminder.triggered: %s", str(exc))

    return {"status": "ERROR"}
