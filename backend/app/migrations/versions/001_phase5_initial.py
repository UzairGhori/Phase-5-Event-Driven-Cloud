"""Phase V initial schema — users, tasks, tags, task_tags, audit_logs, tsvector

Revision ID: 001_phase5
Revises: None
Create Date: 2026-02-22

Task: T-A004 — Alembic migration for all Phase V tables
Spec: §10 (Data Model), FR-027–FR-034, FR-036, FR-044, FR-048
Plan: §9.1 (Database Schema), §9.2 (Migration Strategy)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_phase5"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Users table (Phase II baseline) ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- Tasks table (Phase V extended) ---
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("user_id", sa.String(36), nullable=False),
        # Phase V new fields
        sa.Column("due_date", sa.DateTime, nullable=True),
        sa.Column("recurrence_pattern", sa.String(20), nullable=True),
        sa.Column("recurrence_interval", sa.Integer, nullable=True, server_default="1"),
        sa.Column("recurrence_ends_at", sa.DateTime, nullable=True),
        sa.Column("source_task_id", sa.String(36), nullable=True),
        sa.Column("reminder_at", sa.DateTime, nullable=True),
        sa.Column("reminder_sent", sa.Boolean, nullable=False, server_default="false"),
        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_index("ix_tasks_source_task_id", "tasks", ["source_task_id"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    op.create_index("ix_tasks_status", "tasks", ["status"])

    # --- tsvector column for full-text search (FR-036) ---
    op.execute(
        "ALTER TABLE tasks ADD COLUMN search_vector tsvector"
    )
    op.execute(
        "CREATE INDEX ix_tasks_search_vector ON tasks USING GIN (search_vector)"
    )

    # --- Trigger to auto-update search_vector on INSERT/UPDATE ---
    op.execute("""
        CREATE OR REPLACE FUNCTION tasks_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_tasks_search_vector
        BEFORE INSERT OR UPDATE OF title, description ON tasks
        FOR EACH ROW EXECUTE FUNCTION tasks_search_vector_update();
    """)

    # --- Tags table (FR-033, FR-034, FR-048) ---
    op.create_table(
        "tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("slug", sa.String(60), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_tags_slug", "tags", ["slug"])
    op.create_index("ix_tags_user_id", "tags", ["user_id"])
    op.create_unique_constraint("ix_tag_slug_user", "tags", ["slug", "user_id"])

    # --- TaskTags junction table (many-to-many) ---
    op.create_table(
        "task_tags",
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("tags.id"), primary_key=True),
    )

    # --- AuditLogs table (FR-044) ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", sa.JSON, nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_tasks_search_vector ON tasks")
    op.execute("DROP FUNCTION IF EXISTS tasks_search_vector_update()")
    op.drop_table("audit_logs")
    op.drop_table("task_tags")
    op.drop_table("tags")
    op.drop_table("tasks")
    op.drop_table("users")
