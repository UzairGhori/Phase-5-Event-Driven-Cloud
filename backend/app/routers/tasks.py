# Task: T-A007 (due_date, reminder, recurrence in CRUD)
# Task: T-A008 (overdue endpoint and filter)
# Task: T-A009 (full-text search with tsvector)
# Task: T-A010 (multi-criteria filtering)
# Task: T-A011 (multi-field sorting)
# Task: T-A012 (pagination)
# Task: T-B003 (wire event publishing into Task API CRUD)
# Spec: §11.1, FR-027–FR-040, FR-043
# Plan: §2.1 (Task Endpoints, Query Parameters), §3.2 (Publisher Matrix)

import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlmodel import Session, case, func, select

from backend.app.database import get_session
from backend.app.dependencies.auth import get_current_user
from backend.app.events.publisher import publish_audit_event, publish_event
from backend.app.events.schemas import (
    EventEnvelope,
    ReminderScheduledData,
    TaskCompletedData,
    TaskCreatedData,
    TaskDeletedData,
    TaskUpdatedData,
)
from backend.app.events.topics import (
    REMINDER_SCHEDULED,
    TASK_COMPLETED,
    TASK_CREATED,
    TASK_DELETED,
    TASK_UPDATED,
)
from backend.app.middleware.correlation import get_correlation_id
from backend.app.middleware.metrics import tasks_completed_total, tasks_created_total
from backend.app.models.tag import Tag, TaskTag
from backend.app.models.task import (
    PaginatedTaskResponse,
    PriorityEnum,
    StatusEnum,
    Task,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from backend.app.models.user import User
from backend.app.search.tsvector import search_filter

router = APIRouter(prefix="/api", tags=["tasks"])

PRIORITY_ORDER = {
    PriorityEnum.low.value: 0,
    PriorityEnum.medium.value: 1,
    PriorityEnum.high.value: 2,
    PriorityEnum.critical.value: 3,
}


def _validate_task_dates(
    due_date: Optional[datetime],
    reminder_at: Optional[datetime],
    recurrence_ends_at: Optional[datetime],
):
    """Validate date relationships per Spec §11.1 and §12 US1."""
    if reminder_at and not due_date:
        raise HTTPException(
            status_code=422,
            detail="Reminder requires a due date",
        )
    if reminder_at and due_date and reminder_at >= due_date:
        raise HTTPException(
            status_code=422,
            detail="Reminder must be before due date",
        )
    if due_date:
        due_aware = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
        if due_aware < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=422,
                detail="Due date must be in the future",
            )
    if recurrence_ends_at and due_date and recurrence_ends_at <= due_date:
        raise HTTPException(
            status_code=422,
            detail="Recurrence end date must be after due date",
        )


def _build_task_response(task: Task, session: Session) -> TaskResponse:
    """Build TaskResponse with computed is_overdue and tags."""
    tag_rows = session.exec(
        select(Tag).join(TaskTag, TaskTag.tag_id == Tag.id).where(
            TaskTag.task_id == task.id
        )
    ).all()
    tags = [
        {"id": t.id, "name": t.name, "slug": t.slug, "color": t.color}
        for t in tag_rows
    ]
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        user_id=task.user_id,
        due_date=task.due_date,
        is_overdue=task.is_overdue,
        recurrence_pattern=task.recurrence_pattern,
        recurrence_interval=task.recurrence_interval,
        recurrence_ends_at=task.recurrence_ends_at,
        source_task_id=task.source_task_id,
        reminder_at=task.reminder_at,
        reminder_sent=task.reminder_sent,
        tags=tags,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# --- T-A012: GET /api/tasks with search, filter, sort, pagination ---

@router.get("/tasks", response_model=PaginatedTaskResponse)
def list_tasks(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    # T-A010: Filters
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    tag: Optional[list[str]] = Query(None),
    due_before: Optional[datetime] = Query(None),
    due_after: Optional[datetime] = Query(None),
    overdue: Optional[bool] = Query(None),
    # T-A009: Search
    search: Optional[str] = Query(None),
    # T-A011: Sort
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    # T-A012: Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """GET /api/tasks — Enhanced with search, filter, sort, pagination.
    Spec §11.1, FR-036, FR-037, FR-038."""

    query = select(Task).where(Task.user_id == current_user.id)

    # T-A010: Apply filters
    if status_filter:
        query = query.where(Task.status == status_filter)
    if priority:
        query = query.where(Task.priority == priority)
    if due_before:
        query = query.where(Task.due_date <= due_before)
    if due_after:
        query = query.where(Task.due_date >= due_after)
    if overdue is True:
        now = datetime.now(timezone.utc)
        query = query.where(
            Task.due_date < now,
            Task.status != StatusEnum.completed.value,
        )
    if tag:
        for tag_slug in tag:
            tag_obj = session.exec(
                select(Tag).where(
                    Tag.slug == tag_slug, Tag.user_id == current_user.id
                )
            ).first()
            if tag_obj:
                query = query.where(
                    Task.id.in_(
                        select(TaskTag.task_id).where(TaskTag.tag_id == tag_obj.id)
                    )
                )

    # T-A009: Apply search
    if search:
        sf = search_filter(search)
        if sf is not None:
            query = query.where(sf)

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # T-A011: Apply sort
    if sort_by == "priority":
        priority_case = case(
            (Task.priority == PriorityEnum.low.value, 0),
            (Task.priority == PriorityEnum.medium.value, 1),
            (Task.priority == PriorityEnum.high.value, 2),
            (Task.priority == PriorityEnum.critical.value, 3),
        )
        order_col = priority_case.desc() if sort_order == "desc" else priority_case.asc()
    elif sort_by == "due_date":
        if sort_order == "asc":
            order_col = case(
                (Task.due_date.is_(None), 1),  # type: ignore
                else_=0,
            ).asc()
            query = query.order_by(order_col, Task.due_date.asc())  # type: ignore
            # Skip the generic ordering below
            order_col = None
        else:
            order_col = case(
                (Task.due_date.is_(None), 1),  # type: ignore
                else_=0,
            ).desc()
            query = query.order_by(Task.due_date.desc(), order_col)  # type: ignore
            order_col = None
    elif sort_by == "title":
        order_col = Task.title.desc() if sort_order == "desc" else Task.title.asc()  # type: ignore
    else:  # default: created_at
        order_col = Task.created_at.desc() if sort_order == "desc" else Task.created_at.asc()

    if order_col is not None:
        query = query.order_by(order_col)

    # T-A012: Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    tasks = session.exec(query).all()
    items = [_build_task_response(t, session) for t in tasks]
    total_pages = max(1, math.ceil(total / page_size))

    return PaginatedTaskResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# --- T-A008: GET /api/tasks/overdue ---

@router.get("/tasks/overdue", response_model=PaginatedTaskResponse)
def list_overdue_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """GET /api/tasks/overdue — List overdue tasks. Spec §11.2, FR-028."""
    now = datetime.now(timezone.utc)
    query = select(Task).where(
        Task.user_id == current_user.id,
        Task.due_date < now,
        Task.status != StatusEnum.completed.value,
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    offset = (page - 1) * page_size
    tasks = session.exec(
        query.order_by(Task.due_date.asc()).offset(offset).limit(page_size)  # type: ignore
    ).all()

    items = [_build_task_response(t, session) for t in tasks]
    total_pages = max(1, math.ceil(total / page_size))

    return PaginatedTaskResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# --- T-A007 + T-B003: POST /api/tasks ---

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """POST /api/tasks — Create task with new fields. Spec §11.1.
    Events: task.created + audit.log (+ reminder.scheduled if reminder_at).
    Plan §3.4 Flow 1."""
    _validate_task_dates(body.due_date, body.reminder_at, body.recurrence_ends_at)

    task = Task(
        title=body.title,
        description=body.description,
        status=body.status or StatusEnum.pending.value,
        priority=body.priority or PriorityEnum.medium.value,
        user_id=current_user.id,
        due_date=body.due_date,
        reminder_at=body.reminder_at,
        recurrence_pattern=body.recurrence_pattern,
        recurrence_interval=body.recurrence_interval or 1,
        recurrence_ends_at=body.recurrence_ends_at,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Handle tag associations
    if body.tag_ids:
        if len(body.tag_ids) > 10:
            raise HTTPException(status_code=422, detail="Maximum 10 tags per task")
        for tid in body.tag_ids:
            tag = session.exec(
                select(Tag).where(Tag.id == tid, Tag.user_id == current_user.id)
            ).first()
            if tag:
                session.add(TaskTag(task_id=task.id, tag_id=tid))
        session.commit()

    tasks_created_total.labels(service="task-api").inc()

    # T-B003: Publish events (non-blocking via background tasks)
    correlation_id = get_correlation_id()
    created_envelope = EventEnvelope(
        event_type="task.created",
        correlation_id=correlation_id,
        user_id=current_user.id,
        data=TaskCreatedData(
            task_id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=str(task.due_date) if task.due_date else None,
            tags=[tid for tid in (body.tag_ids or [])],
            recurrence={"pattern": task.recurrence_pattern, "interval": task.recurrence_interval, "ends_at": str(task.recurrence_ends_at) if task.recurrence_ends_at else None} if task.recurrence_pattern else None,
        ).model_dump(),
    )
    background_tasks.add_task(publish_event, TASK_CREATED, created_envelope)
    background_tasks.add_task(publish_audit_event, created_envelope)

    # Publish reminder.scheduled if reminder_at set (Plan §3.4 Flow 1)
    if task.reminder_at:
        reminder_envelope = EventEnvelope(
            event_type="reminder.scheduled",
            correlation_id=correlation_id,
            user_id=current_user.id,
            data=ReminderScheduledData(
                task_id=task.id,
                remind_at=str(task.reminder_at),
                task_title=task.title,
                task_due_date=str(task.due_date) if task.due_date else None,
            ).model_dump(),
        )
        background_tasks.add_task(publish_event, REMINDER_SCHEDULED, reminder_envelope)

    return _build_task_response(task, session)


# --- T-A007: GET /api/tasks/{task_id} ---

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """GET /api/tasks/{task_id}. Constitution §II: 404 for other users."""
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _build_task_response(task, session)


# --- T-A007 + T-B003: PATCH /api/tasks/{task_id} ---

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    body: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """PATCH /api/tasks/{task_id} — Partial update. Spec §11.1.
    Events: task.updated + audit.log (+ reminder.scheduled if reminder_at changed)."""
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    changes = {}
    update_data = body.model_dump(exclude_unset=True)

    new_due = update_data.get("due_date", task.due_date)
    new_reminder = update_data.get("reminder_at", task.reminder_at)
    new_recurrence_ends = update_data.get("recurrence_ends_at", task.recurrence_ends_at)
    _validate_task_dates(new_due, new_reminder, new_recurrence_ends)

    for field, value in update_data.items():
        if field == "tag_ids":
            continue
        old_value = getattr(task, field)
        if old_value != value:
            changes[field] = {"old": str(old_value) if old_value else None, "new": str(value) if value else None}
            setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Handle tag_ids update
    if "tag_ids" in update_data and update_data["tag_ids"] is not None:
        existing = session.exec(
            select(TaskTag).where(TaskTag.task_id == task_id)
        ).all()
        for assoc in existing:
            session.delete(assoc)
        for tid in update_data["tag_ids"][:10]:
            tag = session.exec(
                select(Tag).where(Tag.id == tid, Tag.user_id == current_user.id)
            ).first()
            if tag:
                session.add(TaskTag(task_id=task_id, tag_id=tid))
        session.commit()

    # T-B003: Publish events
    if changes:
        correlation_id = get_correlation_id()
        updated_envelope = EventEnvelope(
            event_type="task.updated",
            correlation_id=correlation_id,
            user_id=current_user.id,
            data=TaskUpdatedData(task_id=task.id, changes=changes).model_dump(),
        )
        background_tasks.add_task(publish_event, TASK_UPDATED, updated_envelope)
        background_tasks.add_task(publish_audit_event, updated_envelope)

        # Publish reminder.scheduled if reminder_at changed
        if "reminder_at" in changes and task.reminder_at:
            reminder_envelope = EventEnvelope(
                event_type="reminder.scheduled",
                correlation_id=correlation_id,
                user_id=current_user.id,
                data=ReminderScheduledData(
                    task_id=task.id,
                    remind_at=str(task.reminder_at),
                    task_title=task.title,
                    task_due_date=str(task.due_date) if task.due_date else None,
                ).model_dump(),
            )
            background_tasks.add_task(publish_event, REMINDER_SCHEDULED, reminder_envelope)

    return _build_task_response(task, session)


# --- T-B003: PATCH /api/tasks/{task_id}/complete ---

@router.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """PATCH /api/tasks/{task_id}/complete — Mark task completed.
    Events: task.completed + audit.log. Plan §3.4 Flow 2."""
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = StatusEnum.completed.value
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)

    tasks_completed_total.labels(service="task-api").inc()

    correlation_id = get_correlation_id()
    completed_envelope = EventEnvelope(
        event_type="task.completed",
        correlation_id=correlation_id,
        user_id=current_user.id,
        data=TaskCompletedData(
            task_id=task.id,
            title=task.title,
            completed_at=str(task.updated_at),
            has_recurrence=task.has_recurrence,
            recurrence_pattern=task.recurrence_pattern,
            recurrence_interval=task.recurrence_interval,
            recurrence_ends_at=str(task.recurrence_ends_at) if task.recurrence_ends_at else None,
            current_due_date=str(task.due_date) if task.due_date else None,
        ).model_dump(),
    )
    background_tasks.add_task(publish_event, TASK_COMPLETED, completed_envelope)
    background_tasks.add_task(publish_audit_event, completed_envelope)

    return _build_task_response(task, session)


# --- T-B003: DELETE /api/tasks/{task_id} ---

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """DELETE /api/tasks/{task_id}. Events: task.deleted + audit.log."""
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    had_reminders = task.reminder_at is not None
    had_recurrence = task.has_recurrence
    title = task.title

    # Delete tag associations first
    assocs = session.exec(
        select(TaskTag).where(TaskTag.task_id == task_id)
    ).all()
    for a in assocs:
        session.delete(a)

    session.delete(task)
    session.commit()

    correlation_id = get_correlation_id()
    deleted_envelope = EventEnvelope(
        event_type="task.deleted",
        correlation_id=correlation_id,
        user_id=current_user.id,
        data=TaskDeletedData(
            task_id=task_id,
            title=title,
            had_reminders=had_reminders,
            had_recurrence=had_recurrence,
        ).model_dump(),
    )
    background_tasks.add_task(publish_event, TASK_DELETED, deleted_envelope)
    background_tasks.add_task(publish_audit_event, deleted_envelope)

    return None
