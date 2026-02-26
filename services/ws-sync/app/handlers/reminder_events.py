# Task: T-A024 — WebSocket reminder event handler
# Plan: §2.6, §3.3

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events/reminder-triggered")
async def handle_reminder_triggered(request: Request) -> dict[str, str]:
    """Push reminder.triggered event to WebSocket clients."""
    body = await request.json()
    data = body.get("data", body)
    user_id = data.get("user_id", "")
    event_data = data.get("data", data)

    message = {
        "type": "reminder.triggered",
        "data": event_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.send_to_user(user_id, message)
    logger.info("Pushed reminder.triggered to user %s", user_id)
    return {"status": "OK"}
