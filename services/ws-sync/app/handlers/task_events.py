# Task: T-A024 — WebSocket task event handlers
# Plan: §2.6, §3.3

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def _push_event(event_type: str, data: dict) -> dict[str, str]:
    """Push event to all WebSocket clients for the user."""
    user_id = data.get("user_id", "")
    event_data = data.get("data", data)

    message = {
        "type": event_type,
        "data": event_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.send_to_user(user_id, message)
    logger.info("Pushed %s to user %s", event_type, user_id)
    return {"status": "OK"}


@router.post("/events/task-created")
async def handle_task_created(request: Request) -> dict[str, str]:
    body = await request.json()
    data = body.get("data", body)
    return await _push_event("task.created", data)


@router.post("/events/task-updated")
async def handle_task_updated(request: Request) -> dict[str, str]:
    body = await request.json()
    data = body.get("data", body)
    return await _push_event("task.updated", data)


@router.post("/events/task-completed")
async def handle_task_completed(request: Request) -> dict[str, str]:
    body = await request.json()
    data = body.get("data", body)
    return await _push_event("task.completed", data)


@router.post("/events/task-deleted")
async def handle_task_deleted(request: Request) -> dict[str, str]:
    body = await request.json()
    data = body.get("data", body)
    return await _push_event("task.deleted", data)
