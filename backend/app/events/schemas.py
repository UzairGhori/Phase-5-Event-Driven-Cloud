# Task: T-B001 — Define event envelope schema and data schemas
# Spec: §8.3 (Event Schemas), FR-043
# Plan: §3.1 (Kafka Topics)

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Common event envelope. Spec §8.3, FR-043.

    All events follow this wrapper with event metadata.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source: str = "task-api"
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    data: dict[str, Any]


# --- Event Data Schemas (Spec §8.3) ---

class TaskCreatedData(BaseModel):
    """Data payload for task.created event. Spec §8.3."""
    task_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    recurrence: Optional[dict] = None


class TaskUpdatedData(BaseModel):
    """Data payload for task.updated event. Spec §8.3."""
    task_id: str
    changes: dict[str, dict[str, Any]]


class TaskCompletedData(BaseModel):
    """Data payload for task.completed event. Spec §8.3."""
    task_id: str
    title: str
    completed_at: str
    has_recurrence: bool
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = None
    recurrence_ends_at: Optional[str] = None
    current_due_date: Optional[str] = None


class TaskDeletedData(BaseModel):
    """Data payload for task.deleted event. Spec §8.3."""
    task_id: str
    title: str
    had_reminders: bool
    had_recurrence: bool


class ReminderScheduledData(BaseModel):
    """Data payload for reminder.scheduled event. Spec §8.3."""
    task_id: str
    reminder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    remind_at: str
    task_title: str
    task_due_date: Optional[str] = None


class ReminderTriggeredData(BaseModel):
    """Data payload for reminder.triggered event. Spec §8.3."""
    task_id: str
    reminder_id: str
    triggered_at: str
    task_title: str
    action: str = "log"
