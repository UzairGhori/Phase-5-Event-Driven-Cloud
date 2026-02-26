# Task: T-A026 — Extended MCP tools for Chat API
# Spec: FR-047, Clarification #12
# Plan: §2.2 (Extended MCP Tools)

import logging
from typing import Any

from app.dapr_client import invoke_task_api
from app.mcp.schemas import (
    AddTagParams,
    AddTaskParams,
    ListTasksParams,
    SearchTasksParams,
    UpdateTaskParams,
)

logger = logging.getLogger(__name__)


async def add_task(params: AddTaskParams, auth_header: str) -> dict[str, Any]:
    """Create a new task via Task API. Supports due_date, reminder, recurrence, tags."""
    data = params.model_dump(exclude_none=True)
    result = await invoke_task_api(
        method="api/tasks",
        data=data,
        http_method="POST",
        headers={"Authorization": auth_header},
    )
    return result or {"error": "Failed to create task"}


async def update_task(params: UpdateTaskParams, auth_header: str) -> dict[str, Any]:
    """Update an existing task. Supports due_date, reminder, tags."""
    task_id = params.task_id
    data = params.model_dump(exclude_none=True, exclude={"task_id"})
    result = await invoke_task_api(
        method=f"api/tasks/{task_id}",
        data=data,
        http_method="PATCH",
        headers={"Authorization": auth_header},
    )
    return result or {"error": "Failed to update task"}


async def complete_task(task_id: str, auth_header: str) -> dict[str, Any]:
    """Mark a task as completed."""
    result = await invoke_task_api(
        method=f"api/tasks/{task_id}/complete",
        data={},
        http_method="PATCH",
        headers={"Authorization": auth_header},
    )
    return result or {"error": "Failed to complete task"}


async def delete_task(task_id: str, auth_header: str) -> dict[str, Any]:
    """Delete a task."""
    result = await invoke_task_api(
        method=f"api/tasks/{task_id}",
        http_method="DELETE",
        headers={"Authorization": auth_header},
    )
    return result or {"error": "Failed to delete task"}


async def list_tasks(params: ListTasksParams, auth_header: str) -> dict[str, Any]:
    """List tasks with search, filters, and sorting."""
    query_params = {}
    for key, val in params.model_dump(exclude_none=True).items():
        query_params[key] = str(val)

    result = await invoke_task_api(
        method="api/tasks",
        http_method="GET",
        headers={"Authorization": auth_header},
        params=query_params,
    )
    return result or {"error": "Failed to list tasks"}


async def search_tasks(params: SearchTasksParams, auth_header: str) -> dict[str, Any]:
    """Full-text search for tasks."""
    result = await invoke_task_api(
        method="api/tasks",
        http_method="GET",
        headers={"Authorization": auth_header},
        params={"search": params.query},
    )
    return result or {"error": "Failed to search tasks"}


async def add_tag(params: AddTagParams, auth_header: str) -> dict[str, Any]:
    """Create a new tag."""
    data = params.model_dump(exclude_none=True)
    result = await invoke_task_api(
        method="api/tags",
        data=data,
        http_method="POST",
        headers={"Authorization": auth_header},
    )
    return result or {"error": "Failed to create tag"}


async def list_tags(auth_header: str) -> dict[str, Any]:
    """List all user tags."""
    result = await invoke_task_api(
        method="api/tags",
        http_method="GET",
        headers={"Authorization": auth_header},
    )
    return result or {"error": "Failed to list tags"}


# Tool registry for the agent
TOOLS = {
    "add_task": {"handler": add_task, "schema": AddTaskParams},
    "update_task": {"handler": update_task, "schema": UpdateTaskParams},
    "complete_task": {"handler": complete_task, "schema": None},
    "delete_task": {"handler": delete_task, "schema": None},
    "list_tasks": {"handler": list_tasks, "schema": ListTasksParams},
    "search_tasks": {"handler": search_tasks, "schema": SearchTasksParams},
    "add_tag": {"handler": add_tag, "schema": AddTagParams},
    "list_tags": {"handler": list_tags, "schema": None},
}
