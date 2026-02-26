# Task: T-B004 — Event schemas for WS Sync Service (copy from Task API)
# Spec: §8.3
# WS Sync subscribes to: task.created, task.updated, task.completed,
#   task.deleted, reminder.triggered

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


class TaskCreatedData(BaseModel):
    task_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    recurrence: Optional[dict] = None


class TaskUpdatedData(BaseModel):
    task_id: str
    changes: dict[str, dict[str, Any]]


class TaskCompletedData(BaseModel):
    task_id: str
    title: str
    completed_at: str
    has_recurrence: bool
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = None
    recurrence_ends_at: Optional[str] = None
    current_due_date: Optional[str] = None


class TaskDeletedData(BaseModel):
    task_id: str
    title: str
    had_reminders: bool
    had_recurrence: bool


class ReminderTriggeredData(BaseModel):
    task_id: str
    reminder_id: str
    triggered_at: str
    task_title: str
    action: str = "log"
