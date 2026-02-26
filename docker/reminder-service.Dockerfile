# Task: T-D001 — Reminder Service Dockerfile (multi-stage)
# Spec: NFR-025
# Plan: §6.3

FROM python:3.12-slim AS deps
WORKDIR /app
COPY services/reminder/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY services/reminder/app/ ./app/

USER appuser
EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
