# Task: T-A025 — Chat API endpoint
# Spec: FR-046, FR-047
# Plan: §2.2

import json
import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.agents.todo_agent import handle_tool_call
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[dict] = Field(default_factory=list)


def get_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_id: str = Depends(get_user_id),
):
    """POST /api/chat — AI-powered task assistant.

    Processes natural language and invokes MCP tools as needed.
    """
    auth_header = f"Bearer {credentials.credentials}"

    # Simple keyword-based routing for common operations
    message = body.message.lower().strip()
    tool_results = []

    if any(kw in message for kw in ["list task", "show task", "my task", "all task"]):
        result = await handle_tool_call("list_tasks", {}, auth_header)
        tool_results.append({"tool": "list_tasks", "result": result})

    elif any(kw in message for kw in ["list tag", "show tag", "my tag"]):
        result = await handle_tool_call("list_tags", {}, auth_header)
        tool_results.append({"tool": "list_tags", "result": result})

    elif "search" in message:
        query = body.message.replace("search", "").replace("for", "").strip()
        if query:
            result = await handle_tool_call("search_tasks", {"query": query}, auth_header)
            tool_results.append({"tool": "search_tasks", "result": result})

    elif any(kw in message for kw in ["overdue", "late", "past due"]):
        result = await handle_tool_call("list_tasks", {"overdue": True}, auth_header)
        tool_results.append({"tool": "list_tasks", "result": result})

    if tool_results:
        reply = _format_tool_results(tool_results)
    else:
        reply = (
            "I can help you manage tasks and tags. Try asking me to:\n"
            "- List your tasks\n"
            "- Search for tasks\n"
            "- Show overdue tasks\n"
            "- List your tags\n\n"
            "For more complex operations, use the API directly."
        )

    return ChatResponse(reply=reply, tool_calls=tool_results)


def _format_tool_results(results: list[dict]) -> str:
    """Format tool call results into a readable response."""
    parts = []
    for r in results:
        data = r["result"]
        if isinstance(data, dict) and "error" in data:
            parts.append(f"Error: {data['error']}")
        elif isinstance(data, dict) and "items" in data:
            items = data["items"]
            if not items:
                parts.append("No items found.")
            else:
                for item in items[:10]:
                    title = item.get("title", item.get("name", ""))
                    status = item.get("status", "")
                    line = f"- {title}"
                    if status:
                        line += f" [{status}]"
                    parts.append(line)
                total = data.get("total", len(items))
                if total > 10:
                    parts.append(f"...and {total - 10} more")
        elif isinstance(data, list):
            for item in data[:10]:
                name = item.get("name", item.get("title", ""))
                parts.append(f"- {name}")
        else:
            parts.append(json.dumps(data, indent=2, default=str))
    return "\n".join(parts) if parts else "Done."
