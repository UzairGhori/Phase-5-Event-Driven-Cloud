# Task: T-A016 — Reminder Service configuration
# Spec: §7.2, FR-029
# Plan: §2.3

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "reminder-service"
    SERVICE_PORT: int = 8002
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3500"))
    TASK_API_APP_ID: str = "task-api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
