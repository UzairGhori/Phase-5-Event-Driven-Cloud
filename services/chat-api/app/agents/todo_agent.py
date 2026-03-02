# Task: T-A025 — Todo Agent using OpenAI Agents SDK
# Spec: FR-046, FR-047
# Plan: §2.2

import logging
from typing import Any

from app.mcp.tools import (
    add_tag,
    add_task,
    complete_task,
    delete_task,
    list_tags,
    list_tasks,
    search_tasks,
    update_task,
)
from app.mcp.schemas import (
    AddTagParams,
    AddTaskParams,
    ListTasksParams,
    SearchTasksParams,
    UpdateTaskParams,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful todo assistant. You can manage tasks and tags for the user.

Available actions:
- add_task: Create a new task (title required, optional: description, priority, due_date, reminder_at, recurrence_pattern, recurrence_interval, tag_ids)
- update_task: Update a task (task_id required, optional: title, description, status, priority, due_date, reminder_at, tag_ids)
- complete_task: Mark a task as completed (task_id required)
- delete_task: Delete a task (task_id required)
- list_tasks: List tasks with filters (optional: search, status, priority, tag, due_before, due_after, overdue, sort_by, sort_order)
- search_tasks: Full-text search (query required)
- add_tag: Create a tag (name required, optional: color)
- list_tags: List all tags

When the user asks to manage tasks, use the appropriate tool. Be concise and helpful."""


async def handle_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    auth_header: str,
) -> dict[str, Any]:
    """Route tool calls to the appropriate handler."""
    if tool_name == "add_task":
        return await add_task(AddTaskParams(**arguments), auth_header)
    elif tool_name == "update_task":
        return await update_task(UpdateTaskParams(**arguments), auth_header)
    elif tool_name == "complete_task":
        return await complete_task(arguments["task_id"], auth_header)
    elif tool_name == "delete_task":
        return await delete_task(arguments["task_id"], auth_header)
    elif tool_name == "list_tasks":
        return await list_tasks(ListTasksParams(**arguments), auth_header)
    elif tool_name == "search_tasks":
        return await search_tasks(SearchTasksParams(**arguments), auth_header)
    elif tool_name == "add_tag":
        return await add_tag(AddTagParams(**arguments), auth_header)
    elif tool_name == "list_tags":
        return await list_tags(auth_header)
    else:
        return {"error": f"Unknown tool: {tool_name}"}
