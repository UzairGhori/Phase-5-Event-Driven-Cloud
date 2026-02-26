# Task: T-A001 — Extend Task model with due_date, recurrence, reminder fields
# Spec: §10.1 (Extended Task Entity), FR-027, FR-028, FR-030, FR-032
# Plan: §9.1 (Database Schema), §1.1 (Task API responsibility)

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Column, Field, SQLModel, String


class PriorityEnum(str, enum.Enum):
    """Task priority levels. FR-032: critical level added."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class StatusEnum(str, enum.Enum):
    """Task status values."""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class RecurrencePattern(str, enum.Enum):
    """Recurrence patterns. FR-030: daily, weekly, monthly."""
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class Task(SQLModel, table=True):
    """Extended Task entity per Spec §10.1.

    New fields (Phase V): due_date, recurrence_pattern, recurrence_interval,
    recurrence_ends_at, source_task_id, reminder_at, reminder_sent, search_vector.
    Extended: priority now includes 'critical'.
    Computed: is_overdue (query-time, not stored).
    """
    __tablename__ = "tasks"

    # --- Existing fields ---
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: str = Field(default=StatusEnum.pending.value, max_length=20)
    priority: str = Field(default=PriorityEnum.medium.value, max_length=20)
    user_id: str = Field(index=True, max_length=36)

    # --- New fields (Phase V) ---
    due_date: Optional[datetime] = Field(default=None)  # FR-027
    recurrence_pattern: Optional[str] = Field(default=None, max_length=20)  # FR-030
    recurrence_interval: Optional[int] = Field(default=1)  # e.g., every 2 weeks
    recurrence_ends_at: Optional[datetime] = Field(default=None)
    source_task_id: Optional[str] = Field(
        default=None, index=True, max_length=36
    )  # Parent recurring task reference
    reminder_at: Optional[datetime] = Field(default=None)  # FR-029
    reminder_sent: bool = Field(default=False)  # Whether reminder was triggered

    # search_vector is managed via raw SQL trigger (tsvector column).
    # SQLModel does not natively support tsvector; handled in migration T-A004.

    # --- Timestamps ---
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def is_overdue(self) -> bool:
        """FR-028: Computed at query time — NOT stored.
        True when due_date < now() AND status != completed.
        Spec §10.1, Clarification #5."""
        if self.due_date is None:
            return False
        if self.status == StatusEnum.completed.value:
            return False
        now = datetime.now(timezone.utc)
        due = self.due_date if self.due_date.tzinfo else self.due_date.replace(
            tzinfo=timezone.utc
        )
        return due < now

    @property
    def has_recurrence(self) -> bool:
        """Helper: True if this task has recurrence fields set."""
        return self.recurrence_pattern is not None


# --- Pydantic schemas for API request/response ---

class TaskCreate(SQLModel):
    """Request body for POST /api/tasks. Spec §11.1."""
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = Field(default=StatusEnum.pending.value)
    priority: Optional[str] = Field(default=PriorityEnum.medium.value)
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = Field(default=1, ge=1)
    recurrence_ends_at: Optional[datetime] = None
    tag_ids: Optional[list[str]] = Field(default_factory=list)


class TaskUpdate(SQLModel):
    """Request body for PUT/PATCH /api/tasks/{task_id}. Spec §11.1."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = Field(default=None, ge=1)
    recurrence_ends_at: Optional[datetime] = None
    tag_ids: Optional[list[str]] = None


class TaskResponse(SQLModel):
    """Response schema for task endpoints. Includes computed is_overdue."""
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    user_id: str
    due_date: Optional[datetime]
    is_overdue: bool
    recurrence_pattern: Optional[str]
    recurrence_interval: Optional[int]
    recurrence_ends_at: Optional[datetime]
    source_task_id: Optional[str]
    reminder_at: Optional[datetime]
    reminder_sent: bool
    tags: list = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PaginatedTaskResponse(SQLModel):
    """Paginated response for GET /api/tasks. FR-038."""
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
