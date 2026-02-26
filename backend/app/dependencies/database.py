# Task: T-A001 (prerequisite — database dependency re-export)
# Plan: §8 (backend/app/dependencies/database.py)

from backend.app.database import get_session

__all__ = ["get_session"]
