# Task: T-A018 — task.updated handler in Reminder Service
# Spec: §8.1, FR-029
# Plan: §3.3, §4.5

import logging

from fastapi import APIRouter, Request

from app.dapr_client import cancel_job, schedule_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events/task-updated")
async def handle_task_updated(request: Request) -> dict[str, str]:
    """Reschedule Dapr Job if reminder_at changed. No-op otherwise."""
    body = await request.json()
    data = body.get("data", body)
    event_data = data.get("data", data)

    task_id = event_data.get("task_id")
    changes = event_data.get("changes", {})

    reminder_change = changes.get("reminder_at")
    if not reminder_change:
        return {"status": "SKIP"}

    job_name = f"reminder-{task_id}"
    old_val = reminder_change.get("old")
    new_val = reminder_change.get("new")

    # Cancel old job if there was a previous reminder
    if old_val:
        await cancel_job(job_name)

    # Schedule new job if new reminder_at is set
    if new_val:
        job_data = {
            "task_id": task_id,
            "user_id": data.get("user_id", ""),
        }
        await schedule_job(job_name, new_val, job_data)
        logger.info("Rescheduled reminder for task %s to %s", task_id, new_val)
    else:
        logger.info("Removed reminder for task %s", task_id)

    return {"status": "OK"}
