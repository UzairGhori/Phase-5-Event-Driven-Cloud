# Task: T-D001 — Task API Dockerfile (multi-stage)
# Spec: NFR-025
# Plan: §6.3

# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY backend/ ./backend/

USER appuser
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
