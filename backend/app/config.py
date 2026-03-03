# Task: T-A001 (prerequisite — application configuration)
# Spec: §6 (Technology Stack), FR-041 (Dapr Secrets in production)
# Plan: §8 (backend/app/config.py)

import json
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000"]


class Settings(BaseSettings):
    """Application settings. Loaded from env vars or Dapr Secrets (FR-041).

    In Kubernetes, secrets are injected via Dapr secretstores.kubernetes
    or secretstores.azure.keyvault (Plan §4.3).
    In local dev, loaded from environment variables.
    """
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/todo_app",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3500"))
    SERVICE_NAME: str = "task-api"
    CORS_ORIGINS: list[str] = _parse_cors_origins()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
