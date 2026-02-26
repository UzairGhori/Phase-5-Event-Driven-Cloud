# Task: T-B004 — Event schemas for Audit Service (copy from Task API)
# Spec: §8.3

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "task-api"
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    data: dict[str, Any]
