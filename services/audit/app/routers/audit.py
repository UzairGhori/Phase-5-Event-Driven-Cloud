# Task: T-A022 — Audit query endpoints
# Spec: FR-044
# Plan: §2.5

import logging
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, func, select

from app.config import get_settings
from app.database import get_session
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()

router = APIRouter(prefix="/api", tags=["audit"])


def get_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract user_id from JWT. Simplified auth for Audit Service."""
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


@router.get("/audit")
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session),
):
    """GET /api/audit — List user audit logs (paginated)."""
    query = select(AuditLog).where(AuditLog.user_id == user_id)
    total = session.exec(
        select(func.count()).where(AuditLog.user_id == user_id)
    ).one()

    logs = session.exec(
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "items": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "event_data": log.event_data,
                "correlation_id": log.correlation_id,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit/{task_id}")
def get_task_audit_trail(
    task_id: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session),
):
    """GET /api/audit/{task_id} — Audit trail for specific task."""
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.asc())
    ).all()

    # Filter by task_id in event_data
    task_logs = [
        log for log in logs
        if log.event_data.get("task_id") == task_id
    ]

    return {
        "task_id": task_id,
        "events": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "event_data": log.event_data,
                "correlation_id": log.correlation_id,
                "created_at": log.created_at.isoformat(),
            }
            for log in task_logs
        ],
    }
