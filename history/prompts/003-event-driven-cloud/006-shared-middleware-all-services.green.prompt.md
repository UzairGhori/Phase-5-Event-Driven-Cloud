---
id: 006
title: Shared Middleware for All Five Microservices
stage: green
date: 2026-02-23
surface: project
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: Marhaba
command: create shared middleware files
labels: [middleware, correlation, logging, metrics, microservices]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: T-A013, T-A016, T-A020, T-A023, T-A025
  adr: n/a
  pr: n/a
files:
  - services/recurring/app/middleware/correlation.py
  - services/recurring/app/middleware/logging.py
  - services/recurring/app/middleware/metrics.py
  - services/reminder/app/middleware/correlation.py
  - services/reminder/app/middleware/logging.py
  - services/reminder/app/middleware/metrics.py
  - services/audit/app/middleware/correlation.py
  - services/audit/app/middleware/logging.py
  - services/audit/app/middleware/metrics.py
  - services/ws-sync/app/middleware/correlation.py
  - services/ws-sync/app/middleware/logging.py
  - services/ws-sync/app/middleware/metrics.py
  - services/chat-api/app/middleware/correlation.py
  - services/chat-api/app/middleware/logging.py
  - services/chat-api/app/middleware/metrics.py
tests:
  - pending: unit tests for middleware in each service
---

## Prompt

Create the shared middleware files for all 5 microservices. Each service needs 3 middleware files following the same pattern as the Task API middleware (already implemented in `backend/app/middleware/`).

For each service (recurring, reminder, audit, ws-sync, chat-api), create these 3 files:

1. `services/{service}/app/middleware/correlation.py` - Same pattern as backend, using contextvars
2. `services/{service}/app/middleware/logging.py` - Same pattern as backend, with service_name from config
3. `services/{service}/app/middleware/metrics.py` - Same pattern as backend but with the service-specific SERVICE_LABEL

Use `from app.middleware.correlation import get_correlation_id` import pattern since services run containerized with app module on PYTHONPATH.

## Response snapshot

Created all 15 middleware files (3 per service x 5 services) following the exact backend/app/middleware/ pattern:

- **correlation.py**: UUID-based X-Correlation-ID propagation via contextvars, identical across all services except task ID comments
- **logging.py**: JSONFormatter with structured JSON output, RequestLoggingMiddleware for HTTP logging, setup_json_logging() function; each uses service-specific default name (e.g., "recurring-service", "audit-service", "chat-api")
- **metrics.py**: Prometheus Counter/Histogram for HTTP metrics, service-specific business counters (e.g., recurring_tasks_generated, reminders_scheduled_total, websocket_connections_active, chat_requests_total, audit_logs_persisted), /metrics scrape endpoint via FastAPI router

Import pattern: `from app.middleware.correlation import get_correlation_id` -- works for containerized deployments where each service runs from its own root.

## Outcome

- Impact: All 5 microservices now have complete observability middleware matching the Task API pattern
- Tests: Pending -- unit tests for each middleware module
- Files: 15 new files created across 5 service middleware directories
- Next prompts: Wire middleware into each service's main.py, create service-specific handler/router logic
- Reflection: Consistent middleware pattern across all services ensures uniform observability and correlation tracing

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual verification PASS -- all 15 files created with correct content
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Wire middleware into service main.py entry points
