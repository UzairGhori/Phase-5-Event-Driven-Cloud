# Task: T-A005 — Implement Tag CRUD router
# Task: T-A006 — Implement task-tag association endpoints
# Spec: §11.2 (New Endpoints: Tags), FR-033, FR-034, FR-048, FR-049
# Plan: §2.1 (Tag Endpoints)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from backend.app.database import get_session
from backend.app.dependencies.auth import get_current_user
from backend.app.models.tag import (
    Tag,
    TagAssign,
    TagCreate,
    TagResponse,
    TagUpdate,
    TaskTag,
    slugify,
)
from backend.app.models.task import Task
from backend.app.models.user import User

router = APIRouter(prefix="/api", tags=["tags"])

MAX_TAGS_PER_USER = 50  # FR-048
MAX_TAGS_PER_TASK = 10  # FR-048


@router.get("/tags", response_model=list[TagResponse])
def list_tags(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """GET /api/tags — List user's tags with task_count. Spec §11.2."""
    tags = session.exec(
        select(Tag).where(Tag.user_id == current_user.id)
    ).all()
    result = []
    for tag in tags:
        count = session.exec(
            select(func.count()).where(TaskTag.tag_id == tag.id)
        ).one()
        result.append(
            TagResponse(
                id=tag.id,
                name=tag.name,
                slug=tag.slug,
                color=tag.color,
                user_id=tag.user_id,
                created_at=tag.created_at,
                task_count=count,
            )
        )
    return result


@router.post("/tags", response_model=TagResponse, status_code=201)
def create_tag(
    body: TagCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """POST /api/tags — Create tag. Spec §11.2, FR-048 (max 50/user)."""
    # Enforce max 50 tags per user
    user_tag_count = session.exec(
        select(func.count()).where(Tag.user_id == current_user.id)
    ).one()
    if user_tag_count >= MAX_TAGS_PER_USER:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_TAGS_PER_USER} tags per user reached",
        )

    slug = slugify(body.name)
    # Check duplicate (case-insensitive via slug)
    existing = session.exec(
        select(Tag).where(Tag.slug == slug, Tag.user_id == current_user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tag already exists")

    tag = Tag(
        name=body.name,
        slug=slug,
        color=body.color,
        user_id=current_user.id,
    )
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return TagResponse(
        id=tag.id,
        name=tag.name,
        slug=tag.slug,
        color=tag.color,
        user_id=tag.user_id,
        created_at=tag.created_at,
        task_count=0,
    )


@router.patch("/tags/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: str,
    body: TagUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """PATCH /api/tags/{tag_id} — Update tag. Spec §11.2, FR-049."""
    tag = session.exec(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if body.name is not None:
        new_slug = slugify(body.name)
        if new_slug != tag.slug:
            conflict = session.exec(
                select(Tag).where(
                    Tag.slug == new_slug,
                    Tag.user_id == current_user.id,
                    Tag.id != tag_id,
                )
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="Tag name conflicts with existing tag")
            tag.slug = new_slug
        tag.name = body.name

    if body.color is not None:
        tag.color = body.color

    session.add(tag)
    session.commit()
    session.refresh(tag)

    count = session.exec(
        select(func.count()).where(TaskTag.tag_id == tag.id)
    ).one()
    return TagResponse(
        id=tag.id,
        name=tag.name,
        slug=tag.slug,
        color=tag.color,
        user_id=tag.user_id,
        created_at=tag.created_at,
        task_count=count,
    )


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(
    tag_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """DELETE /api/tags/{tag_id} — Delete tag and associations. Spec §11.2."""
    tag = session.exec(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Delete all task-tag associations
    associations = session.exec(
        select(TaskTag).where(TaskTag.tag_id == tag_id)
    ).all()
    for assoc in associations:
        session.delete(assoc)

    session.delete(tag)
    session.commit()
    return None


# --- Task-Tag Association Endpoints (T-A006) ---

@router.post("/tasks/{task_id}/tags", status_code=200)
def add_tags_to_task(
    task_id: str,
    body: TagAssign,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """POST /api/tasks/{task_id}/tags — Add tags to task. Spec §11.2, FR-048."""
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    current_count = session.exec(
        select(func.count()).where(TaskTag.task_id == task_id)
    ).one()

    if current_count + len(body.tag_ids) > MAX_TAGS_PER_TASK:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_TAGS_PER_TASK} tags per task exceeded",
        )

    for tid in body.tag_ids:
        tag = session.exec(
            select(Tag).where(Tag.id == tid, Tag.user_id == current_user.id)
        ).first()
        if not tag:
            raise HTTPException(status_code=404, detail=f"Tag {tid} not found")
        existing = session.exec(
            select(TaskTag).where(
                TaskTag.task_id == task_id, TaskTag.tag_id == tid
            )
        ).first()
        if not existing:
            session.add(TaskTag(task_id=task_id, tag_id=tid))

    session.commit()
    return {"status": "ok", "task_id": task_id}


@router.delete("/tasks/{task_id}/tags/{tag_id}", status_code=204)
def remove_tag_from_task(
    task_id: str,
    tag_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """DELETE /api/tasks/{task_id}/tags/{tag_id} — Remove tag. Spec §11.2."""
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    assoc = session.exec(
        select(TaskTag).where(
            TaskTag.task_id == task_id, TaskTag.tag_id == tag_id
        )
    ).first()
    if assoc:
        session.delete(assoc)
        session.commit()
    return None
