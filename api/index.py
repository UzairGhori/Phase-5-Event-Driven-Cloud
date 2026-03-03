# Vercel Serverless entry point for the FastAPI backend
import os

os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from backend.app.main import app  # noqa: E402, F401
