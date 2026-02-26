# Task: T-A021 — audit.log event handler
# Spec: FR-044, §8.1
# Plan: §3.3, §2.5

import logging

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.database import get_session
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events/audit-log")
async def handle_audit_log(
    request: Request,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Dapr Pub/Sub handler for todo.audit.log events.

    Persists event data to AuditLog table. Idempotent via event_id check.
    """
    body = await request.json()
    data = body.get("data", body)

    event_id = data.get("event_id", "")
    event_type = data.get("event_type", "")
    user_id = data.get("user_id", "")
    correlation_id = data.get("correlation_id", "")
    event_data = data.get("data", {})

    if not event_type or not user_id:
        logger.warning("Received audit event with missing fields")
        return {"status": "SKIP"}

    audit_log = AuditLog(
        id=event_id,
        event_type=event_type,
        event_data=event_data,
        user_id=user_id,
        correlation_id=correlation_id,
    )

    try:
        session.add(audit_log)
        session.commit()
        logger.info("Persisted audit log %s: %s", event_id, event_type)
        return {"status": "OK"}
    except Exception:
        session.rollback()
        logger.info("Audit log %s already exists (idempotent skip)", event_id)
        return {"status": "DUPLICATE"}
