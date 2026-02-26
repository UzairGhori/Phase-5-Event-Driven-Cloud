# Task: T-A023 — WebSocket endpoint
# Plan: §2.6

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.websocket.auth import validate_ws_token
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/tasks")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WS /ws/tasks?token={jwt} — Real-time task updates.

    JWT validated on connect. Invalid token → close 4001.
    """
    user_id = validate_ws_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive; server-push only
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
