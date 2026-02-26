# Task: T-A018 — task.deleted handler in Reminder Service
# Spec: §8.1, FR-029
# Plan: §3.3, §4.5

import logging

from fastapi import APIRouter, Request

from app.dapr_client import cancel_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events/task-deleted")
async def handle_task_deleted(request: Request) -> dict[str, str]:
    """Cancel pending Dapr Job when a task is deleted."""
    body = await request.json()
    data = body.get("data", body)
    event_data = data.get("data", data)

    task_id = event_data.get("task_id")
    had_reminders = event_data.get("had_reminders", False)

    if not had_reminders:
        return {"status": "SKIP"}

    job_name = f"reminder-{task_id}"
    await cancel_job(job_name)
    logger.info("Cancelled reminder job for deleted task %s", task_id)
    return {"status": "OK"}
