---
id: 006
title: Microservice Scaffolds and Logic Implementation
stage: green
date: 2026-02-22
surface: claude-code
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: architect
command: continue implementing the microservice scaffolds
labels: [microservices, recurring, reminder, audit, ws-sync, chat-api, T-A013-A026, T-B004]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: T-A013 through T-A026, T-B004
  adr: N/A
  pr: N/A
files:
  - services/recurring/app/main.py (created)
  - services/recurring/app/config.py (created)
  - services/recurring/app/recurrence.py (created - T-A014)
  - services/recurring/app/dapr_client.py (created)
  - services/recurring/app/handlers/task_completed.py (created - T-A015)
  - services/recurring/app/routers/health.py (created)
  - services/recurring/app/middleware/{correlation,logging,metrics}.py (created)
  - services/recurring/app/events/schemas.py (created - T-B004)
  - services/recurring/requirements.txt (created)
  - services/reminder/app/main.py (created)
  - services/reminder/app/config.py (created)
  - services/reminder/app/dapr_client.py (created - schedule/cancel jobs)
  - services/reminder/app/handlers/reminder_scheduled.py (created - T-A017)
  - services/reminder/app/handlers/task_deleted.py (created - T-A018)
  - services/reminder/app/handlers/task_updated.py (created - T-A018)
  - services/reminder/app/jobs/reminder_triggered.py (created - T-A019)
  - services/reminder/app/routers/health.py (created)
  - services/reminder/app/middleware/{correlation,logging,metrics}.py (created)
  - services/reminder/app/events/schemas.py (created - T-B004)
  - services/reminder/requirements.txt (created)
  - services/audit/app/main.py (created)
  - services/audit/app/config.py (created)
  - services/audit/app/database.py (created)
  - services/audit/app/models/audit.py (created - T-A020)
  - services/audit/app/handlers/audit_log.py (created - T-A021)
  - services/audit/app/routers/audit.py (created - T-A022)
  - services/audit/app/routers/health.py (created)
  - services/audit/app/middleware/{correlation,logging,metrics}.py (created)
  - services/audit/app/events/schemas.py (created - T-B004)
  - services/audit/requirements.txt (created)
  - services/ws-sync/app/main.py (created)
  - services/ws-sync/app/config.py (created)
  - services/ws-sync/app/websocket/manager.py (created - T-A023)
  - services/ws-sync/app/websocket/auth.py (created - T-A023)
  - services/ws-sync/app/routers/ws.py (created - T-A023)
  - services/ws-sync/app/handlers/task_events.py (created - T-A024)
  - services/ws-sync/app/handlers/reminder_events.py (created - T-A024)
  - services/ws-sync/app/routers/health.py (created)
  - services/ws-sync/app/middleware/{correlation,logging,metrics}.py (created)
  - services/ws-sync/app/events/schemas.py (created - T-B004)
  - services/ws-sync/requirements.txt (created)
  - services/chat-api/app/main.py (created)
  - services/chat-api/app/config.py (created)
  - services/chat-api/app/dapr_client.py (created)
  - services/chat-api/app/agents/todo_agent.py (created - T-A025)
  - services/chat-api/app/mcp/schemas.py (created - T-A026)
  - services/chat-api/app/mcp/tools.py (created - T-A026)
  - services/chat-api/app/routers/chat.py (created - T-A025)
  - services/chat-api/app/routers/health.py (created)
  - services/chat-api/app/middleware/{correlation,logging,metrics}.py (created)
  - services/chat-api/requirements.txt (created)
tests:
  - N/A (service scaffolds, integration tests pending)
---

## Prompt

continue implementing the microservice scaffolds

## Response snapshot

Implemented all 5 microservices (T-A013 through T-A026 + T-B004):

**Recurring Task Service (port 8003)**:
- Scaffold with health probes, middleware, metrics
- `compute_next_due_date()` pure function (daily/weekly/monthly with intervals)
- `task.completed` event handler: checks has_recurrence, computes next due date, creates next instance via Dapr Service Invocation

**Reminder Service (port 8002)**:
- Scaffold with health probes, middleware, metrics
- Dapr client with `schedule_job()` and `cancel_job()` for Jobs API
- `reminder.scheduled` handler: schedules one-time Dapr Job
- `task.deleted` handler: cancels pending job
- `task.updated` handler: reschedules if reminder_at changed
- `reminder-triggered` job callback: checks task status, publishes reminder.triggered event

**Audit Service (port 8004)**:
- Scaffold with DB access, health probes, middleware
- AuditLog SQLModel entity (matches Task API)
- `audit.log` handler: persists events, idempotent via event_id
- Query endpoints: GET /api/audit (paginated), GET /api/audit/{task_id} (trail)

**WebSocket Sync Service (port 8005)**:
- Scaffold with health probes, middleware
- ConnectionManager: tracks connections per user_id
- JWT validation for WebSocket handshake (4001 on invalid)
- Event handlers: task.created/updated/completed/deleted + reminder.triggered → push to WS clients

**Chat API Service (port 8001)**:
- Scaffold with health probes, middleware
- MCP tool schemas (AddTask, UpdateTask, ListTasks, SearchTasks, AddTag)
- 8 MCP tools: add_task, update_task, complete_task, delete_task, list_tasks, search_tasks, add_tag, list_tags
- Chat endpoint with keyword-based routing
- All tools invoke Task API via Dapr Service Invocation

**Event Schemas (T-B004)**: Copied to all 4 consumer services.

## Outcome

- ✅ Impact: All 5 microservices scaffolded with full business logic, 82 Python files created
- 🧪 Tests: No tests yet (infrastructure/scaffolds)
- 📁 Files: 82 Python files + 5 requirements.txt
- 🔁 Next prompts: Create Dockerfiles (T-D001), Dapr component YAMLs (T-C001-C006), K8s manifests (T-D002+)
- 🧠 Reflection: Batch creation approach efficient for cross-cutting concerns (middleware). Each service follows consistent patterns: config → middleware → health → handlers → main.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (manual verification pending)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test each service's import chain with `python -c "from app.main import app"`
