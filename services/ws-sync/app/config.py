# Task: T-A023 — WebSocket Sync Service configuration
# Plan: §2.6

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "ws-sync-service"
    SERVICE_PORT: int = 8005
    DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3500"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
