# Task: T-A002 — Create Tag and TaskTag SQLModel entities
# Spec: §10.2 (Tag Entity), §10.3 (TaskTag), FR-033, FR-034, FR-048
# Plan: §9.1 (Tables: tags, task_tags)

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


def slugify(name: str) -> str:
    """Generate URL-safe slug from tag name. Lowercase, hyphenated."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


class Tag(SQLModel, table=True):
    """User-scoped tag entity. Spec §10.2.

    Unique constraint: (slug, user_id) — each user has unique tag slugs.
    Limits: max 50 tags per user (FR-048, enforced at router level).
    """
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("slug", "user_id", name="ix_tag_slug_user"),
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    name: str = Field(max_length=50)
    slug: str = Field(max_length=60, index=True)
    color: Optional[str] = Field(default=None, max_length=7)  # Hex: #FF5733
    user_id: str = Field(index=True, max_length=36)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class TaskTag(SQLModel, table=True):
    """Many-to-many junction for Task ↔ Tag. Spec §10.3.

    Limits: max 10 tags per task (FR-048, enforced at router level).
    """
    __tablename__ = "task_tags"

    task_id: str = Field(primary_key=True, max_length=36, foreign_key="tasks.id")
    tag_id: str = Field(primary_key=True, max_length=36, foreign_key="tags.id")


# --- Pydantic schemas for API request/response ---

class TagCreate(SQLModel):
    """Request body for POST /api/tags. Spec §11.2."""
    name: str = Field(min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)


class TagUpdate(SQLModel):
    """Request body for PATCH /api/tags/{tag_id}. Spec §11.2, FR-049."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)


class TagResponse(SQLModel):
    """Response schema for tag endpoints. Spec §11.2."""
    id: str
    name: str
    slug: str
    color: Optional[str]
    user_id: str
    created_at: datetime
    task_count: int = 0


class TagAssign(SQLModel):
    """Request body for POST /api/tasks/{task_id}/tags. Spec §11.2."""
    tag_ids: list[str] = Field(max_length=10)
