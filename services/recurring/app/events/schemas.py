# Task: T-B004 — Event schemas for Recurring Service (copy from Task API)
# Spec: §8.3

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

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


class TaskCompletedData(BaseModel):
    task_id: str
    title: str
    completed_at: str
    has_recurrence: bool
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = None
    recurrence_ends_at: Optional[str] = None
    current_due_date: Optional[str] = None
