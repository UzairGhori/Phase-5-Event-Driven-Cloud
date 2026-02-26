# Task: T-A025 — Chat API Service configuration
# Spec: FR-046, FR-047
# Plan: §2.2

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "chat-api"
    SERVICE_PORT: int = 8001
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3500"))
    TASK_API_APP_ID: str = "task-api"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
