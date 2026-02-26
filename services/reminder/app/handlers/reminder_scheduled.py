# Task: T-A017 — reminder.scheduled event handler
# Spec: §9.3 (Dapr Jobs API), FR-029, SC-018
# Plan: §4.5, §2.3

import logging

from fastapi import APIRouter, Request

from app.dapr_client import schedule_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events/reminder-scheduled")
async def handle_reminder_scheduled(request: Request) -> dict[str, str]:
    """Dapr Pub/Sub handler for todo.reminder.scheduled events.

    Schedules a one-time Dapr Job at the specified reminder_at time.
    Job name: reminder-{task_id}. Idempotent (re-scheduling overwrites).
    """
    body = await request.json()
    data = body.get("data", body)
    event_data = data.get("data", data)

    task_id = event_data.get("task_id")
    remind_at = event_data.get("remind_at")
    task_title = event_data.get("task_title", "")

    if not task_id or not remind_at:
        logger.warning("Missing task_id or remind_at in reminder.scheduled event")
        return {"status": "SKIP"}

    job_name = f"reminder-{task_id}"
    job_data = {
        "task_id": task_id,
        "task_title": task_title,
        "remind_at": remind_at,
        "user_id": data.get("user_id", ""),
    }

    success = await schedule_job(job_name, remind_at, job_data)
    if success:
        logger.info("Scheduled reminder job %s for %s", job_name, remind_at)
        return {"status": "OK"}

    logger.error("Failed to schedule reminder job %s", job_name)
    return {"status": "ERROR"}
