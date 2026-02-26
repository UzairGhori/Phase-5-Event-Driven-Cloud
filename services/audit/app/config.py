# Task: T-A020 — Audit Service configuration
# Spec: §10.4, FR-044
# Plan: §2.5

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "audit-service"
    SERVICE_PORT: int = 8004
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3500"))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/todo_app",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
