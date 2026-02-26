# Task: T-A020 — Audit Service database setup
# Spec: §10.4 (AuditLog Entity)

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
