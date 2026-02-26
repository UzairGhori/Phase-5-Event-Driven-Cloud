# Task: T-A026 — MCP tool parameter schemas
# Spec: FR-047, Clarification #12
# Plan: §2.2

from typing import Optional

from pydantic import BaseModel, Field


class AddTaskParams(BaseModel):
    title: str = Field(description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    priority: Optional[str] = Field(default="medium", description="low, medium, high, critical")
    due_date: Optional[str] = Field(default=None, description="ISO 8601 due date")
    reminder_at: Optional[str] = Field(default=None, description="ISO 8601 reminder time")
    recurrence_pattern: Optional[str] = Field(default=None, description="daily, weekly, monthly")
    recurrence_interval: Optional[int] = Field(default=1, description="Recurrence interval")
    tag_ids: Optional[list[str]] = Field(default=None, description="Tag IDs to assign")


class UpdateTaskParams(BaseModel):
    task_id: str = Field(description="Task ID to update")
    title: Optional[str] = Field(default=None, description="New title")
    description: Optional[str] = Field(default=None, description="New description")
    status: Optional[str] = Field(default=None, description="pending, in_progress, completed")
    priority: Optional[str] = Field(default=None, description="low, medium, high, critical")
    due_date: Optional[str] = Field(default=None, description="ISO 8601 due date")
    reminder_at: Optional[str] = Field(default=None, description="ISO 8601 reminder time")
    tag_ids: Optional[list[str]] = Field(default=None, description="Tag IDs to assign")


class ListTasksParams(BaseModel):
    search: Optional[str] = Field(default=None, description="Full-text search query")
    status: Optional[str] = Field(default=None, description="Filter by status")
    priority: Optional[str] = Field(default=None, description="Filter by priority")
    tag: Optional[str] = Field(default=None, description="Filter by tag slug")
    due_before: Optional[str] = Field(default=None, description="Filter tasks due before date")
    due_after: Optional[str] = Field(default=None, description="Filter tasks due after date")
    overdue: Optional[bool] = Field(default=None, description="Filter overdue tasks")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="asc or desc")
    page: int = Field(default=1, description="Page number")
    page_size: int = Field(default=10, description="Items per page")


class SearchTasksParams(BaseModel):
    query: str = Field(description="Full-text search query")


class AddTagParams(BaseModel):
    name: str = Field(description="Tag name")
    color: Optional[str] = Field(default=None, description="Hex color (#FF5733)")
