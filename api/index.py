# Vercel Serverless entry point for the FastAPI backend
# This file wraps the existing FastAPI app for Vercel's Python runtime

from backend.app.main import app  # noqa: F401
