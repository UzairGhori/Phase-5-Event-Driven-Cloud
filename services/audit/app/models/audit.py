# Task: T-A020 — Audit Service AuditLog model
# Spec: §10.4 (AuditLog Entity), FR-044

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    event_type: str = Field(max_length=100)
    event_data: dict = Field(sa_column=Column(JSON, nullable=False))
    user_id: str = Field(index=True, max_length=36)
    correlation_id: str = Field(index=True, max_length=36)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
