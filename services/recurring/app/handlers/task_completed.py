# Task: T-A015 — task.completed event handler in Recurring Service
# Spec: §12 US2 (all 5 acceptance scenarios), FR-031
# Plan: §2.4, §3.3, §3.4 Flow 2

import logging
from datetime import datetime
from fastapi import APIRouter, Request

from app.config import get_settings
from app.dapr_client import invoke_service
from app.middleware.correlation import get_correlation_id
from app.recurrence import compute_next_due_date

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.post("/events/task-completed")
async def handle_task_completed(request: Request) -> dict[str, str]:
    """Dapr Pub/Sub handler for todo.task.completed events.

    Plan §3.4 Flow 2:
    1. Receive task.completed event
    2. Check has_recurrence flag
    3. Compute next due date
    4. Create next task instance via Dapr Service Invocation
    """
    body = await request.json()
    data = body.get("data", body)
    event_data = data.get("data", data)

    has_recurrence = event_data.get("has_recurrence", False)
    if not has_recurrence:
        logger.info("Task %s has no recurrence, skipping", event_data.get("task_id"))
        return {"status": "SKIP"}

    task_id = event_data.get("task_id")
    title = event_data.get("title", "")
    pattern = event_data.get("recurrence_pattern")
    interval = event_data.get("recurrence_interval", 1)
    ends_at_str = event_data.get("recurrence_ends_at")
    current_due_str = event_data.get("current_due_date")

    if not pattern or not current_due_str:
        logger.warning(
            "Missing recurrence fields for task %s: pattern=%s, current_due=%s",
            task_id, pattern, current_due_str,
        )
        return {"status": "SKIP"}

    current_due = datetime.fromisoformat(current_due_str)
    ends_at = datetime.fromisoformat(ends_at_str) if ends_at_str else None

    next_due = compute_next_due_date(current_due, pattern, interval, ends_at)
    if next_due is None:
        logger.info(
            "Recurrence ended for task %s (next due exceeds ends_at)", task_id
        )
        return {"status": "ENDED"}

    # Create next task instance via Dapr Service Invocation
    user_id = data.get("user_id", "")
    new_task_data = {
        "title": title,
        "status": "pending",
        "priority": "medium",
        "due_date": next_due.isoformat(),
        "recurrence_pattern": pattern,
        "recurrence_interval": interval,
        "source_task_id": task_id,
    }
    if ends_at_str:
        new_task_data["recurrence_ends_at"] = ends_at_str

    correlation_id = get_correlation_id()
    result = await invoke_service(
        app_id=settings.TASK_API_APP_ID,
        method="api/tasks",
        data=new_task_data,
        http_method="POST",
        headers={
            "X-Correlation-ID": correlation_id,
            "X-User-ID": user_id,
        },
    )

    if result:
        logger.info(
            "Created recurring task instance for task %s, next due %s",
            task_id, next_due.isoformat(),
        )
        return {"status": "OK"}

    logger.error("Failed to create recurring task instance for task %s", task_id)
    return {"status": "ERROR"}
