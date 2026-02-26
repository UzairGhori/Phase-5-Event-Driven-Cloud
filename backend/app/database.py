# Task: T-A001, T-A004 (database engine and session)
# Spec: §6 (PostgreSQL + SQLModel), FR-051 (local PostgreSQL in Minikube)
# Plan: §9.1 (Database Schema), §9.2 (Migration Strategy)

from sqlmodel import Session, SQLModel, create_engine

from backend.app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create all tables. Used for dev/testing. Production uses Alembic."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency for database sessions."""
    with Session(engine) as session:
        yield session
