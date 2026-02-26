# Task: T-A023 — WebSocket connection manager
# Plan: §2.6

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Track active WebSocket connections per user_id.

    Provides send_to_user() to broadcast events to all connections for a user.
    """

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info("WebSocket connected: user=%s (total=%d)", user_id, self.total_connections)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws is not websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info("WebSocket disconnected: user=%s (total=%d)", user_id, self.total_connections)

    async def send_to_user(self, user_id: str, message: dict[str, Any]):
        """Send JSON message to all connections for a specific user."""
        if user_id not in self._connections:
            return
        stale = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(user_id, ws)

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()
