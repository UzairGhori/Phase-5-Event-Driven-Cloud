# Task: T-A003 — Create AuditLog SQLModel entity
# Spec: §10.4 (AuditLog Entity), FR-044
# Plan: §9.1 (Tables: audit_logs)

import uuid
from datetime import datetime, timezone
from sqlmodel import Column, Field, SQLModel
from sqlalchemy import JSON


class AuditLog(SQLModel, table=True):
    """Immutable record of domain events. Spec §10.4.

    Populated from Kafka events by the Audit Service (Plan §2.5).
    Indexes on user_id and correlation_id (Spec §10.6).
    """
    __tablename__ = "audit_logs"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    event_type: str = Field(max_length=100)  # e.g., "task.created"
    event_data: dict = Field(sa_column=Column(JSON, nullable=False))
    user_id: str = Field(index=True, max_length=36)
    correlation_id: str = Field(index=True, max_length=36)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
