# Tasks: Phase V — Advanced Event-Driven Cloud Deployment

**Input**: `specs/003-event-driven-cloud/spec.md`, `specs/003-event-driven-cloud/plan.md`
**Prerequisites**: spec.md (clarified), plan.md (approved), constitution v2.0.0
**Branch**: `003-event-driven-cloud`
**Date**: 2026-02-22

---

## Format: `[ID] [P?] [Group] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Group]**: Which group this task belongs to (A, B, C, D, E, F, G)
- Every task includes: preconditions, files, expected output, spec/plan references

---

## GROUP A — Advanced Features

### A.1 — Data Model Extensions (Foundation)

---

#### T-A001: ~~Extend Task model with due_date, recurrence, and reminder fields~~ [X] DONE

**Description**: Add new columns to the Task SQLModel entity: `due_date`, `recurrence_pattern`, `recurrence_interval`, `recurrence_ends_at`, `source_task_id`, `reminder_at`, `reminder_sent`. Add `critical` to priority enum. Add computed `is_overdue` property (query-time, not stored).

**Preconditions**: Existing Phase IV `backend/app/models/task.py` exists with base Task model.

**Files to modify**:
- `backend/app/models/task.py` — Add new fields to Task SQLModel

**Expected output**:
- Task model has 7 new nullable fields with correct types and defaults
- Priority enum includes `critical`
- `is_overdue` is a `@property` computed from `due_date < now() AND status != completed`
- No Alembic migration yet (separate task)

**Spec reference**: Spec §10.1 (Extended Task Entity), FR-027, FR-028, FR-030, FR-032
**Plan reference**: Plan §9.1 (Database Schema), Plan §1.1 (Task API responsibility)

---

#### T-A002: ~~Create Tag and TaskTag SQLModel entities~~ [X] DONE

**Description**: Create `Tag` model (id, name, slug, color, user_id, created_at) and `TaskTag` junction model (task_id, tag_id). Add unique constraint on `(slug, user_id)`.

**Preconditions**: T-A001 complete (Task model extended).

**Files to modify**:
- `backend/app/models/tag.py` — Create new file with Tag and TaskTag models

**Expected output**:
- Tag entity with all fields per spec §10.2
- TaskTag junction entity with composite PK per spec §10.3
- Unique constraint on `(slug, user_id)`
- Auto-generated slug from name (lowercase, hyphenated)

**Spec reference**: Spec §10.2 (Tag Entity), §10.3 (TaskTag), FR-033, FR-034, FR-048
**Plan reference**: Plan §9.1 (Tables: tags, task_tags)

---

#### T-A003: ~~Create AuditLog SQLModel entity~~ [X] DONE

**Description**: Create `AuditLog` model (id, event_type, event_data as JSON, user_id, correlation_id, created_at).

**Preconditions**: None (independent model).

**Files to modify**:
- `backend/app/models/audit.py` — Create new file with AuditLog model

**Expected output**:
- AuditLog entity with all fields per spec §10.4
- JSON column for event_data
- Indexes on user_id and correlation_id

**Spec reference**: Spec §10.4 (AuditLog Entity), FR-044
**Plan reference**: Plan §9.1 (Tables: audit_logs)

---

#### T-A004: ~~Create Alembic migration for all new models~~ [X] DONE

**Description**: Generate and verify an Alembic migration that adds: new Task columns, Tag table, TaskTag table, AuditLog table, search_vector tsvector column with GIN index, and all indexes from spec §10.6. Add tsvector trigger to auto-update search_vector on title/description change.

**Preconditions**: T-A001, T-A002, T-A003 complete.

**Files to modify**:
- `backend/app/migrations/versions/` — New migration file
- `backend/app/database.py` — Ensure tsvector trigger is created

**Expected output**:
- Migration applies cleanly on empty DB and on existing Phase IV DB
- All 8 indexes from spec §10.6 are created
- tsvector trigger auto-updates `search_vector` on INSERT/UPDATE of title or description
- Migration is idempotent (safe to re-run)

**Spec reference**: Spec §10.6 (Indexes), FR-035
**Plan reference**: Plan §9.2 (Migration Strategy)

---

### A.2 — Tag CRUD Endpoints

---

#### T-A005: ~~Implement Tag CRUD router~~ [X] DONE

**Description**: Create `backend/app/routers/tags.py` with: `GET /api/tags` (list with task_count), `POST /api/tags` (create with slug auto-gen), `PATCH /api/tags/{tag_id}` (rename/recolor), `DELETE /api/tags/{tag_id}` (cascade delete associations). All endpoints require JWT auth, scoped to user. Enforce max 50 tags per user on create.

**Preconditions**: T-A002 complete (Tag model exists).

**Files to modify**:
- `backend/app/routers/tags.py` — Create new file
- `backend/app/main.py` — Register tags router

**Expected output**:
- All 4 tag endpoints functional per spec §11.2
- 409 on duplicate tag name (case-insensitive)
- 404 on tag belonging to another user
- Max 50 tags per user enforced (422 on exceed)
- DELETE cascades to task_tags

**Spec reference**: Spec §11.2 (New Endpoints: Tags), FR-033, FR-048, FR-049
**Plan reference**: Plan §2.1 (Tag Endpoints)

---

#### T-A006: ~~Implement task-tag association endpoints~~ [X] DONE

**Description**: Create `POST /api/tasks/{task_id}/tags` (add tags to task) and `DELETE /api/tasks/{task_id}/tags/{tag_id}` (remove tag from task). Enforce max 10 tags per task.

**Preconditions**: T-A005 complete (Tag CRUD exists).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add tag association endpoints

**Expected output**:
- Add tags returns updated task with tags array
- Remove tag returns 204
- Max 10 tags per task enforced (422 on exceed)
- Validates tag ownership (user_id match)

**Spec reference**: Spec §11.2 (POST /api/tasks/{task_id}/tags, DELETE), FR-034, FR-048
**Plan reference**: Plan §2.1 (Task Endpoints: tag operations)

---

### A.3 — Due Dates, Overdue, Reminders

---

#### T-A007: ~~Extend Task CRUD for due_date and reminder_at fields~~ [X] DONE

**Description**: Update `POST /api/tasks` and `PUT/PATCH /api/tasks/{task_id}` to accept `due_date`, `reminder_at`, `recurrence_pattern`, `recurrence_interval`, `recurrence_ends_at`, and `tag_ids`. Add validation: due_date must be in future, reminder_at must be before due_date, reminder_at requires due_date.

**Preconditions**: T-A001 complete (Task model extended), T-A006 complete (tag associations).

**Files to modify**:
- `backend/app/routers/tasks.py` — Extend create/update endpoints

**Expected output**:
- Task creation accepts all new fields
- Validation errors return 422 with descriptive messages
- `is_overdue` computed in response serialization
- `tag_ids` creates TaskTag associations on create

**Spec reference**: Spec §11.1 (POST /api/tasks enhanced), FR-027, FR-029, FR-030
**Plan reference**: Plan §2.1 (Task Endpoints)

---

#### T-A008: ~~Implement overdue tasks endpoint and filter~~ [X] DONE

**Description**: Create `GET /api/tasks/overdue` that returns tasks where `due_date < now() AND status != completed`. Also add `overdue=true` query parameter support to `GET /api/tasks`.

**Preconditions**: T-A007 complete (due_date field accepted).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add overdue endpoint and filter

**Expected output**:
- `GET /api/tasks/overdue` returns paginated overdue tasks
- `GET /api/tasks?overdue=true` filters correctly
- `is_overdue` is always correct in response (computed at query time)

**Spec reference**: Spec §11.2 (GET /api/tasks/overdue), FR-028
**Plan reference**: Plan §2.1 (Task Endpoints)

---

### A.4 — Search, Filter, Sort, Pagination

---

#### T-A009: ~~Implement full-text search with tsvector~~ [X] DONE

**Description**: Add `search` query parameter to `GET /api/tasks`. Use PostgreSQL `to_tsquery('english', ...)` against `search_vector` column. Search matches on title and description with English stemming.

**Preconditions**: T-A004 complete (tsvector column and GIN index exist).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add search parameter
- `backend/app/search/tsvector.py` — Create helper for building tsquery

**Expected output**:
- `GET /api/tasks?search=groceries` returns matching tasks
- Stemming works ("running" matches "run")
- Search combines with other filters
- Performance < 300ms for 1000 tasks per user

**Spec reference**: Spec §11.1 (GET /api/tasks: search param), FR-035, SC-019
**Plan reference**: Plan §2.1 (Query Parameters), Plan §8 (search/tsvector.py)

---

#### T-A010: ~~Implement multi-criteria filtering~~ [X] DONE

**Description**: Add filter query parameters to `GET /api/tasks`: `status`, `priority`, `tag` (repeatable), `due_before`, `due_after`, `overdue`. All filters are combinable (AND logic).

**Preconditions**: T-A006 complete (tags exist), T-A008 complete (overdue logic).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add filter parameters

**Expected output**:
- All 6 filter params work independently and in combination
- `tag` param accepts slug and is repeatable (AND: task must have ALL specified tags)
- `due_before`/`due_after` accept ISO 8601 datetime
- Empty result set returns 200 with empty items array

**Spec reference**: Spec §11.1 (GET /api/tasks: filter params), FR-036
**Plan reference**: Plan §2.1 (Query Parameters)

---

#### T-A011: ~~Implement multi-field sorting~~ [X] DONE

**Description**: Add `sort_by` and `sort_order` query parameters to `GET /api/tasks`. Support sort fields: `created_at`, `due_date`, `priority`, `title`. Priority sort uses ordinal: critical > high > medium > low. Tasks with null due_date sort last when sorting by due_date.

**Preconditions**: T-A007 complete (due_date exists).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add sort parameters

**Expected output**:
- All 4 sort fields work with asc/desc
- Priority sort follows correct ordinal
- Null due_date sorts last (asc) or first (desc)
- Default: `sort_by=created_at&sort_order=desc`

**Spec reference**: Spec §11.1 (GET /api/tasks: sort params), FR-037
**Plan reference**: Plan §2.1 (Query Parameters)

---

#### T-A012: ~~Implement pagination~~ [X] DONE

**Description**: Add `page` and `page_size` query parameters to `GET /api/tasks`. Return paginated response with `items`, `total`, `page`, `page_size`, `total_pages`.

**Preconditions**: T-A010 complete (filters exist, pagination wraps them).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add pagination logic

**Expected output**:
- Default: page=1, page_size=20
- Max page_size=100 (422 if exceeded)
- Response includes total count and total_pages
- Works correctly with all filters and sort

**Spec reference**: Spec §11.1 (GET /api/tasks: pagination), FR-038
**Plan reference**: Plan §2.1 (Query Parameters)

---

### A.5 — Recurring Task Service

---

#### T-A013: ~~Create Recurring Task Service scaffold~~ [X] DONE

**Description**: Create `services/recurring/` directory with FastAPI app, config, health router, middleware (correlation, logging, metrics). The service is event-driven only — no external API.

**Preconditions**: None (new service).

**Files to modify**:
- `services/recurring/app/main.py` — Create FastAPI app
- `services/recurring/app/config.py` — Service configuration
- `services/recurring/app/routers/health.py` — Health/readiness probes
- `services/recurring/app/middleware/correlation.py` — Correlation ID middleware
- `services/recurring/app/middleware/logging.py` — Structured JSON logging
- `services/recurring/app/middleware/metrics.py` — Prometheus metrics
- `services/recurring/requirements.txt` — Dependencies

**Expected output**:
- FastAPI app starts on port 8003
- `GET /api/health` returns `{"status": "healthy"}`
- `GET /api/ready` returns readiness status
- Structured JSON logging active

**Spec reference**: Spec §7.2 (Recurring Task Service), FR-031
**Plan reference**: Plan §1.1 (Service #4), Plan §2.4

---

#### T-A014: ~~Implement recurrence date computation logic~~ [X] DONE

**Description**: Create `services/recurring/app/recurrence.py` with pure function `compute_next_due_date(current_due_date, pattern, interval, ends_at)`. Supports daily, weekly, monthly patterns with configurable interval. Returns None if next date exceeds ends_at.

**Preconditions**: T-A013 complete (service scaffold).

**Files to modify**:
- `services/recurring/app/recurrence.py` — Create new file

**Expected output**:
- `compute_next_due_date("2026-02-28", "weekly", 1, None)` → `"2026-03-07"`
- `compute_next_due_date("2026-02-28", "weekly", 2, None)` → `"2026-03-14"`
- `compute_next_due_date("2026-02-28", "daily", 1, None)` → `"2026-03-01"`
- `compute_next_due_date("2026-02-28", "monthly", 1, None)` → `"2026-03-28"`
- Returns None if computed date > ends_at

**Spec reference**: Spec §12 US2 (Recurring Task Lifecycle), FR-031
**Plan reference**: Plan §2.4 (Internal Flow)

---

#### T-A015: ~~Implement task.completed event handler in Recurring Service~~ [X] DONE

**Description**: Create `services/recurring/app/handlers/task_completed.py`. On receiving a `task.completed` event with recurrence fields, compute next due date, then call Task API via Dapr Service Invocation to create the next instance with `source_task_id` set.

**Preconditions**: T-A014 complete (recurrence logic), T-B003 complete (Dapr Pub/Sub handler wiring).

**Files to modify**:
- `services/recurring/app/handlers/task_completed.py` — Create event handler
- `services/recurring/app/dapr_client.py` — Dapr Service Invocation helper
- `services/recurring/app/main.py` — Register handler route

**Expected output**:
- Consumes `todo.task.completed` events
- Skips events where `has_recurrence=false`
- Creates next task instance via Dapr Service Invocation to Task API
- New instance has: advanced due_date, same recurrence fields, source_task_id, status=pending
- No new instance if next due_date > recurrence_ends_at
- Idempotent (checks event_id via Dapr state store)

**Spec reference**: Spec §12 US2 (all 5 acceptance scenarios), FR-031
**Plan reference**: Plan §2.4, Plan §3.3 (Subscriber Matrix: Recurring Service), Plan §3.4 Flow 2

---

### A.6 — Reminder Service

---

#### T-A016: ~~Create Reminder Service scaffold~~ [X] DONE

**Description**: Create `services/reminder/` directory with FastAPI app, config, health router, middleware.

**Preconditions**: None (new service).

**Files to modify**:
- `services/reminder/app/main.py` — Create FastAPI app
- `services/reminder/app/config.py` — Service configuration
- `services/reminder/app/routers/health.py` — Health/readiness probes
- `services/reminder/app/middleware/correlation.py`
- `services/reminder/app/middleware/logging.py`
- `services/reminder/app/middleware/metrics.py`
- `services/reminder/requirements.txt`

**Expected output**:
- FastAPI app starts on port 8002
- Health/readiness probes functional
- Structured JSON logging active

**Spec reference**: Spec §7.2 (Reminder Service), FR-029
**Plan reference**: Plan §1.1 (Service #3), Plan §2.3

---

#### T-A017: ~~Implement reminder.scheduled event handler~~ [X] DONE

**Description**: Create `services/reminder/app/handlers/reminder_scheduled.py`. On receiving `todo.reminder.scheduled` event, schedule a one-time Dapr Job at the specified `reminder_at` time with job name `reminder-{task_id}`.

**Preconditions**: T-A016 complete, T-C003 complete (Dapr Jobs API available).

**Files to modify**:
- `services/reminder/app/handlers/reminder_scheduled.py` — Create handler
- `services/reminder/app/dapr_client.py` — Dapr Jobs API helper
- `services/reminder/app/main.py` — Register handler route

**Expected output**:
- Consumes `todo.reminder.scheduled` events
- Schedules Dapr Job with `dueTime` set to `reminder_at`
- Job name: `reminder-{task_id}`
- Idempotent (re-scheduling overwrites existing job)

**Spec reference**: Spec §9.3 (Jobs API), FR-029, SC-018
**Plan reference**: Plan §4.5 (Dapr Jobs API Usage), Plan §2.3

---

#### T-A018: ~~Implement task.deleted and task.updated handlers in Reminder Service~~ [X] DONE

**Description**: Create handlers for `todo.task.deleted` (cancel pending Dapr Job) and `todo.task.updated` (reschedule if reminder_at changed).

**Preconditions**: T-A017 complete (reminder scheduling works).

**Files to modify**:
- `services/reminder/app/handlers/task_deleted.py` — Cancel Dapr Job
- `services/reminder/app/handlers/task_updated.py` — Reschedule if reminder_at changed
- `services/reminder/app/main.py` — Register handler routes

**Expected output**:
- On task.deleted: DELETE Dapr Job `reminder-{task_id}`
- On task.updated with reminder_at change: cancel old job, schedule new
- On task.updated without reminder_at change: no-op
- Graceful handling if job doesn't exist (not an error)

**Spec reference**: Spec §8.1 (Domain Events: task.deleted, task.updated consumers), FR-029
**Plan reference**: Plan §3.3 (Subscriber Matrix: Reminder Service), Plan §4.5

---

#### T-A019: ~~Implement Dapr Jobs callback (reminder triggered)~~ [X] DONE

**Description**: Create `services/reminder/app/jobs/reminder_triggered.py`. When Dapr fires the job callback, check task status via Service Invocation to Task API. If not completed, publish `todo.reminder.triggered` event. Task API then sets `reminder_sent=true`.

**Preconditions**: T-A017 complete (jobs are scheduled).

**Files to modify**:
- `services/reminder/app/jobs/reminder_triggered.py` — Job callback handler
- `services/reminder/app/main.py` — Register callback route

**Expected output**:
- Dapr calls `POST /jobs/reminder-triggered` when job fires
- Service checks task status via Dapr Service Invocation
- If task not completed: publishes `todo.reminder.triggered` event
- If task already completed: logs and discards (no notification)
- Reminder Service publishes to `todo.reminder.triggered`

**Spec reference**: Spec §8.3 (reminder.triggered event schema), Spec Edge Cases (reminder fires on completed task)
**Plan reference**: Plan §3.4 Flow 3 (Reminder Firing), Plan §4.5

---

### A.7 — Audit Service

---

#### T-A020: ~~Create Audit Service scaffold~~ [X] DONE

**Description**: Create `services/audit/` directory with FastAPI app, config, health router, middleware, and AuditLog model.

**Preconditions**: None (new service).

**Files to modify**:
- `services/audit/app/main.py` — Create FastAPI app
- `services/audit/app/config.py` — Service configuration
- `services/audit/app/models/audit.py` — AuditLog SQLModel
- `services/audit/app/routers/health.py` — Health/readiness probes
- `services/audit/app/middleware/correlation.py`
- `services/audit/app/middleware/logging.py`
- `services/audit/app/middleware/metrics.py`
- `services/audit/requirements.txt`

**Expected output**:
- FastAPI app starts on port 8004
- AuditLog model matches spec §10.4
- Health/readiness probes functional

**Spec reference**: Spec §10.4 (AuditLog Entity), FR-044
**Plan reference**: Plan §1.1 (Service #5), Plan §2.5, Plan §12 (Spec Deviation: Audit Service)

---

#### T-A021: ~~Implement audit.log event handler~~ [X] DONE

**Description**: Create `services/audit/app/handlers/audit_log.py`. Consumes `todo.audit.log` events and persists to AuditLog table.

**Preconditions**: T-A020 complete (Audit Service scaffold).

**Files to modify**:
- `services/audit/app/handlers/audit_log.py` — Create handler
- `services/audit/app/main.py` — Register handler route

**Expected output**:
- Consumes `todo.audit.log` events
- Persists to AuditLog table with all fields
- Idempotent (event_id dedup via Dapr state store)

**Spec reference**: FR-044, Spec §8.1 (Audit Log consumer)
**Plan reference**: Plan §3.3 (Subscriber Matrix: Audit Service), Plan §2.5

---

#### T-A022: ~~Implement audit query endpoints~~ [X] DONE

**Description**: Create `services/audit/app/routers/audit.py` with `GET /api/audit` (list user audit logs) and `GET /api/audit/{task_id}` (audit trail for specific task). Both require JWT auth, scoped to user.

**Preconditions**: T-A021 complete (audit events persisted).

**Files to modify**:
- `services/audit/app/routers/audit.py` — Create audit query router
- `services/audit/app/main.py` — Register router

**Expected output**:
- `GET /api/audit` returns paginated audit events for authenticated user
- `GET /api/audit/{task_id}` returns audit trail for specific task (filtered by user_id)
- JWT auth required, user isolation enforced

**Spec reference**: FR-044
**Plan reference**: Plan §2.5 (Audit Service endpoints)

---

### A.8 — WebSocket Sync Service

---

#### T-A023: ~~Create WebSocket Sync Service scaffold~~ [X] DONE

**Description**: Create `services/ws-sync/` directory with FastAPI app, config, health router, middleware, WebSocket connection manager.

**Preconditions**: None (new service).

**Files to modify**:
- `services/ws-sync/app/main.py` — Create FastAPI app
- `services/ws-sync/app/config.py` — Service configuration
- `services/ws-sync/app/routers/health.py` — Health/readiness probes
- `services/ws-sync/app/routers/ws.py` — WebSocket endpoint
- `services/ws-sync/app/websocket/manager.py` — Connection manager (user_id → connections)
- `services/ws-sync/app/websocket/auth.py` — JWT validation for WS
- `services/ws-sync/app/middleware/correlation.py`
- `services/ws-sync/app/middleware/logging.py`
- `services/ws-sync/app/middleware/metrics.py`
- `services/ws-sync/requirements.txt`

**Expected output**:
- FastAPI app starts on port 8005
- `WS /ws/tasks?token={jwt}` accepts WebSocket connections
- JWT validated on connect; invalid token → close with 4001
- Connection manager tracks active connections per user_id
- `active_websocket_connections` Prometheus gauge exposed

**Spec reference**: Plan §12 (Spec Deviation: WebSocket Sync Service added)
**Plan reference**: Plan §1.1 (Service #6), Plan §2.6

---

#### T-A024: ~~Implement WebSocket event handlers~~ [X] DONE

**Description**: Create event handlers that consume Kafka events and push to connected WebSocket clients. Handle: task.created, task.updated, task.completed, task.deleted, reminder.triggered.

**Preconditions**: T-A023 complete (WS service scaffold).

**Files to modify**:
- `services/ws-sync/app/handlers/task_events.py` — Task event handlers
- `services/ws-sync/app/handlers/reminder_events.py` — Reminder event handler
- `services/ws-sync/app/main.py` — Register handler routes

**Expected output**:
- Each event type pushes JSON message to all connected clients for that user_id
- WebSocket message format: `{"type": "task.created", "data": {...}, "timestamp": "..."}`
- Graceful handling of disconnected clients (remove from manager)

**Spec reference**: Plan §12 (Spec Deviation)
**Plan reference**: Plan §2.6 (WebSocket Message Format), Plan §3.3 (WS Sync subscriptions)

---

### A.9 — Chat API Service

---

#### T-A025: ~~Create Chat API Service scaffold~~ [X] DONE

**Description**: Create `services/chat-api/` directory with FastAPI app, config, health router, middleware. Migrate Phase III chatbot code into this service.

**Preconditions**: Existing Phase III/IV chatbot code available.

**Files to modify**:
- `services/chat-api/app/main.py` — Create FastAPI app
- `services/chat-api/app/config.py` — Service configuration
- `services/chat-api/app/routers/chat.py` — Chat endpoint
- `services/chat-api/app/routers/health.py` — Health/readiness probes
- `services/chat-api/app/agents/todo_agent.py` — OpenAI Agents SDK agent
- `services/chat-api/app/middleware/correlation.py`
- `services/chat-api/app/middleware/logging.py`
- `services/chat-api/app/middleware/metrics.py`
- `services/chat-api/requirements.txt`

**Expected output**:
- FastAPI app starts on port 8001
- Chat endpoint functional
- Health/readiness probes operational
- Existing Phase III chatbot behavior preserved

**Spec reference**: FR-046, FR-047
**Plan reference**: Plan §1.1 (Service #2), Plan §2.2, Plan §12 (Chat API separation)

---

#### T-A026: ~~Extend MCP tools for new features~~ [X] DONE

**Description**: Update MCP tools in Chat API to support new fields. Extend `add_task` (due_date, reminder_at, recurrence, tag_ids), `list_tasks` (search, filters, sort), `update_task` (due_date, reminder_at, tag_ids). Add new tools: `add_tag`, `list_tags`, `search_tasks`.

**Preconditions**: T-A025 complete (Chat API scaffold).

**Files to modify**:
- `services/chat-api/app/mcp/tools.py` — Extend existing tools, add new tools
- `services/chat-api/app/mcp/schemas.py` — Update tool parameter schemas

**Expected output**:
- `add_task` accepts due_date, reminder_at, recurrence_pattern, recurrence_interval, tag_ids
- `list_tasks` accepts search, status, priority, tag, due_before, due_after, overdue, sort_by, sort_order
- `update_task` accepts due_date, reminder_at, tag_ids
- New tools: `add_tag` (name, color), `list_tags`, `search_tasks` (query)
- All tools call Task API via Dapr Service Invocation

**Spec reference**: FR-047, Spec §12 Clarification #12
**Plan reference**: Plan §2.2 (Extended MCP Tools)

---

### A.10 — Frontend Updates

---

#### T-A027: ~~[P] Create Next.js Route Handlers (SSR Proxy)~~ [X] DONE

**Description**: Create API route handlers in `frontend/src/app/api/` that proxy requests to backend services via Dapr Service Invocation. Routes: tasks/*, tags/*, chat/*, auth/*.

**Preconditions**: Existing Phase IV frontend.

**Files to modify**:
- `frontend/src/app/api/tasks/route.ts` — Proxy to task-api
- `frontend/src/app/api/tags/route.ts` — Proxy to task-api
- `frontend/src/app/api/chat/route.ts` — Proxy to chat-api
- `frontend/src/app/api/auth/[...path]/route.ts` — Proxy to task-api auth
- `frontend/src/lib/dapr.ts` — Dapr service invocation helper (server-side)

**Expected output**:
- All frontend API calls go through Route Handlers
- Route Handlers use Dapr Service Invocation in K8s, direct HTTP in dev
- Browser never calls FastAPI directly
- JWT token forwarded in proxy requests

**Spec reference**: FR-050, Spec Clarification #3 (SSR Proxy pattern)
**Plan reference**: Plan §4.6 (Service Invocation Patterns), Plan §8 (frontend structure)

---

#### T-A028: ~~[P] Build tag management UI components~~ [X] DONE

**Description**: Create frontend components for tag management: tag list, create tag dialog, tag picker (for task form), tag badges (on task cards). Use Tailwind CSS.

**Preconditions**: T-A027 complete (SSR proxy routes exist).

**Files to modify**:
- `frontend/src/components/tags/tag-list.tsx`
- `frontend/src/components/tags/tag-create-dialog.tsx`
- `frontend/src/components/tags/tag-picker.tsx`
- `frontend/src/components/tags/tag-badge.tsx`

**Expected output**:
- Tag list displays all user tags with color and task count
- Create dialog with name and color picker
- Tag picker for task create/edit forms (multi-select, max 10)
- Tag badges render on task cards

**Spec reference**: FR-033, FR-034
**Plan reference**: Plan §8 (frontend/src/components/tags/)

---

#### T-A029: ~~[P] Build search, filter, and sort UI components~~ [X] DONE

**Description**: Create filter bar, search input, sort dropdown, and pagination controls. Integrate with `GET /api/tasks` query parameters via Route Handlers.

**Preconditions**: T-A027 complete (SSR proxy routes exist).

**Files to modify**:
- `frontend/src/components/search/search-input.tsx`
- `frontend/src/components/filters/filter-bar.tsx`
- `frontend/src/components/filters/sort-controls.tsx`
- `frontend/src/components/ui/pagination.tsx`

**Expected output**:
- Search input with debounced query
- Filter bar with dropdowns for status, priority, tag, due date range, overdue toggle
- Sort dropdown with 4 fields + asc/desc
- Pagination controls with page numbers

**Spec reference**: FR-036, FR-037, FR-038
**Plan reference**: Plan §8 (frontend/src/components/filters/, search/)

---

#### T-A030: ~~Update task form for due date, reminder, and recurrence~~ [X] DONE

**Description**: Extend the task create/edit form to include: due date picker, reminder datetime picker, recurrence pattern selector (daily/weekly/monthly), recurrence interval input, recurrence end date.

**Preconditions**: T-A027 complete (SSR proxy routes exist).

**Files to modify**:
- `frontend/src/components/tasks/task-form.tsx` — Extend with new fields

**Expected output**:
- Due date picker (calendar + time)
- Reminder picker (disabled if no due_date, must be before due_date)
- Recurrence section (pattern dropdown, interval number, end date)
- Validation matches backend (422 messages shown)

**Spec reference**: FR-027, FR-029, FR-030
**Plan reference**: Plan §8 (frontend/src/components/tasks/)

---

#### T-A031: ~~[P] Integrate WebSocket client for real-time updates~~ [X] DONE

**Description**: Create WebSocket client in `frontend/src/lib/ws.ts` that connects to WS Sync Service. On receiving task events, update the local task list state without page refresh.

**Preconditions**: T-A023 complete (WS Sync Service exists).

**Files to modify**:
- `frontend/src/lib/ws.ts` — WebSocket client with reconnect logic
- `frontend/src/app/dashboard/page.tsx` — Integrate WS updates

**Expected output**:
- WebSocket connects on dashboard mount with JWT token
- Reconnects on disconnect (exponential backoff)
- Task list updates in real-time on create/update/complete/delete events
- Reminder notifications shown as toast/banner

**Spec reference**: Plan §12 (Spec Deviation: WebSocket)
**Plan reference**: Plan §2.6 (WebSocket Message Format), Plan §8 (frontend/src/lib/ws.ts)

---

## GROUP B — Kafka Integration

---

#### T-B001: ~~Define event envelope schema and topic constants~~ [X] DONE

**Description**: Create shared event schema definitions: `EventEnvelope` Pydantic model, individual event data schemas (TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted, ReminderScheduled, ReminderTriggered), and topic name constants.

**Preconditions**: None.

**Files to modify**:
- `backend/app/events/schemas.py` — Event envelope + all data schemas
- `backend/app/events/topics.py` — Topic name constants

**Expected output**:
- `EventEnvelope` with: event_id, event_type, event_version, timestamp, source, correlation_id, user_id, data
- Typed data schemas for each event type matching spec §8.3
- Topic constants: `TASK_CREATED = "todo.task.created"`, etc.
- All 8 topics from plan §3.1 defined

**Spec reference**: Spec §8.3 (Event Schemas), FR-043
**Plan reference**: Plan §3.1 (Kafka Topics)

---

#### T-B002: ~~Implement Dapr Pub/Sub event publisher in Task API~~ [X] DONE

**Description**: Create `backend/app/events/publisher.py` with `publish_event(topic, event_envelope)` function that publishes events via Dapr Pub/Sub HTTP API. Implement retry logic with exponential backoff (3 retries). On all retries exhausted, write to dead-letter table.

**Preconditions**: T-B001 complete (schemas defined).

**Files to modify**:
- `backend/app/events/publisher.py` — Create publish function with retry

**Expected output**:
- `publish_event("todo.task.created", envelope)` publishes via `POST http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/pubsub-kafka/todo.task.created`
- Exponential backoff: 1s, 5s, 25s
- On failure after 3 retries: log error, write to dead-letter table
- Returns immediately if Dapr sidecar not available (database-first pattern)

**Spec reference**: FR-039, FR-040, NFR-018, NFR-020
**Plan reference**: Plan §3.2 (Publisher Matrix), Plan §10.3 (Dead-Letter Handling)

---

#### T-B003: ~~Wire event publishing into Task API CRUD operations~~ [X] DONE

**Description**: Add event publishing calls to all Task API state-changing endpoints. Each operation publishes the appropriate event after successful database persistence. Also publish to `todo.audit.log` for every state change. Publish `todo.reminder.scheduled` when reminder_at is set or changed.

**Preconditions**: T-B002 complete (publisher exists), T-A007 complete (extended Task CRUD).

**Files to modify**:
- `backend/app/routers/tasks.py` — Add publish calls after DB operations

**Expected output**:
- `POST /api/tasks` → publishes `task.created` + `audit.log` (+ `reminder.scheduled` if reminder_at set)
- `PUT/PATCH /api/tasks/{id}` → publishes `task.updated` + `audit.log` (+ `reminder.scheduled` if reminder_at changed)
- `PATCH /api/tasks/{id}/complete` → publishes `task.completed` + `audit.log`
- `DELETE /api/tasks/{id}` → publishes `task.deleted` + `audit.log`
- Event publishing is non-blocking (fire-and-forget with retry)
- All events include correlation_id from request

**Spec reference**: FR-039, FR-043, Spec §8.1 (Domain Events table)
**Plan reference**: Plan §3.2 (Publisher Matrix), Plan §3.4 (Event Flow Diagrams)

---

#### T-B004: ~~[P] Duplicate event schemas into consumer services~~ [X] DONE

**Description**: Copy event envelope and data schemas into each consumer service to maintain independence (no shared library). Services: reminder, recurring, audit, ws-sync.

**Preconditions**: T-B001 complete (schemas defined in backend).

**Files to modify**:
- `services/reminder/app/events/schemas.py` — Copy schemas
- `services/recurring/app/events/schemas.py` — Copy schemas
- `services/audit/app/events/schemas.py` — Copy schemas
- `services/ws-sync/app/events/schemas.py` — Copy schemas

**Expected output**:
- Each service has its own copy of event schemas
- Schemas are identical to backend/app/events/schemas.py
- No cross-service imports

**Spec reference**: FR-043
**Plan reference**: Plan §8 (Structure Decision: "duplicated per service to maintain independence")

---

## GROUP C — Dapr Integration

---

#### T-C001: ~~Create Dapr Pub/Sub Kafka component (local)~~ [X] DONE

**Description**: Create Dapr component YAML for `pubsub-kafka` pointing to local Strimzi Kafka broker (no auth). For Minikube deployment.

**Preconditions**: None.

**Files to modify**:
- `dapr/components/pubsub-kafka-local.yaml` — Local Strimzi config
- `k8s/local/dapr/pubsub-kafka.yaml` — K8s manifest

**Expected output**:
- Component name: `pubsub-kafka`
- Type: `pubsub.kafka`
- Brokers: `strimzi-kafka-bootstrap.kafka:9092`
- authType: `none`
- initialOffset: `oldest`

**Spec reference**: Spec §9.1 (Pub/Sub component), FR-040
**Plan reference**: Plan §4.1 (pubsub-kafka local config)

---

#### T-C002: ~~Create Dapr state store component (PostgreSQL)~~ [X] DONE

**Description**: Create Dapr component YAML for `statestore` using `state.postgresql` (not Redis, per user requirement).

**Preconditions**: None.

**Files to modify**:
- `dapr/components/statestore-postgresql.yaml` — PostgreSQL state store config
- `k8s/local/dapr/statestore-postgresql.yaml` — K8s manifest

**Expected output**:
- Component name: `statestore`
- Type: `state.postgresql`
- connectionString via secretKeyRef
- tableName: `dapr_state`

**Spec reference**: Spec §9.2 (State Management)
**Plan reference**: Plan §4.2 (statestore-postgresql), Plan §12 (Spec Deviation: PostgreSQL not Redis)

---

#### T-C003: ~~Create Dapr secrets store component (Kubernetes)~~ [X] DONE

**Description**: Create Dapr component YAML for `secrets-store` using `secretstores.kubernetes` for local Minikube deployment.

**Preconditions**: None.

**Files to modify**:
- `dapr/components/secrets-kubernetes.yaml` — K8s secrets store config
- `k8s/local/dapr/secrets-kubernetes.yaml` — K8s manifest

**Expected output**:
- Component name: `secrets-store`
- Type: `secretstores.kubernetes`
- Used by all services to retrieve secrets

**Spec reference**: Spec §9.4 (Secrets Management), FR-041
**Plan reference**: Plan §4.3 (secrets-store local config)

---

#### T-C004: ~~Create Dapr subscription manifests~~ [X] DONE

**Description**: Create all Dapr Subscription v2alpha1 manifests that wire topics to service endpoints with correct scopes.

**Preconditions**: None.

**Files to modify**:
- `dapr/components/subscriptions.yaml` — All subscriptions
- `k8s/local/dapr/subscriptions.yaml` — K8s manifest

**Expected output**:
- 11 subscriptions matching plan §3.3 subscriber matrix
- Each subscription has correct topic, route, and scope
- Reminder Service: 3 subscriptions (reminder.scheduled, task.deleted, task.updated)
- Recurring Service: 1 subscription (task.completed)
- Audit Service: 1 subscription (audit.log)
- WS Sync Service: 5 subscriptions (task.created, task.updated, task.completed, task.deleted, reminder.triggered)

**Spec reference**: Spec §8.1 (Domain Events consumers)
**Plan reference**: Plan §4.4 (Dapr Subscriptions — full YAML)

---

#### T-C005: ~~[P] Create Dapr Pub/Sub Kafka component (production)~~ [X] DONE

**Description**: Create Dapr component YAML for `pubsub-kafka` pointing to Redpanda Cloud with SASL/SCRAM auth.

**Preconditions**: None.

**Files to modify**:
- `dapr/components/pubsub-kafka-production.yaml` — Redpanda Cloud config
- `k8s/production/dapr/pubsub-kafka.yaml` — K8s manifest

**Expected output**:
- Component name: `pubsub-kafka`
- Brokers, username, password via secretKeyRef
- authType: `password`
- saslMechanism: `SCRAM-SHA-256`

**Spec reference**: Spec §9.1 (Pub/Sub Kafka config), NFR-023
**Plan reference**: Plan §4.1 (pubsub-kafka production config)

---

#### T-C006: ~~[P] Create Dapr secrets store component (Azure Key Vault)~~ [X] DONE

**Description**: Create Dapr component YAML for `secrets-store` using `secretstores.azure.keyvault` for production AKS.

**Preconditions**: None.

**Files to modify**:
- `dapr/components/secrets-azure-keyvault.yaml` — Azure Key Vault config
- `k8s/production/dapr/secrets-azure-keyvault.yaml` — K8s manifest

**Expected output**:
- Component name: `secrets-store`
- Type: `secretstores.azure.keyvault`
- vaultName, azureClientId, azureTenantId configured

**Spec reference**: Spec §9.4 (Secrets Management — AKS), FR-041
**Plan reference**: Plan §4.3 (secrets-store production config)

---

## GROUP D — Local Deployment (Minikube)

---

#### T-D001: ~~Create Dockerfiles for all services (multi-stage)~~ [X] DONE

**Description**: Create 7 Dockerfiles (task-api, chat-api, reminder, recurring, audit, ws-sync, frontend). Python services use `python:3.12-slim` base, frontend uses `node:22-alpine`. All use multi-stage builds, non-root user.

**Preconditions**: Service source code exists (T-A013, T-A016, T-A020, T-A023, T-A025 complete).

**Files to modify**:
- `docker/task-api.Dockerfile`
- `docker/chat-api.Dockerfile`
- `docker/reminder-service.Dockerfile`
- `docker/recurring-service.Dockerfile`
- `docker/audit-service.Dockerfile`
- `docker/ws-sync-service.Dockerfile`
- `docker/frontend.Dockerfile`

**Expected output**:
- 3-stage build: deps → build → runtime
- Non-root user in runtime stage
- `.dockerignore` excludes tests, docs, etc.
- Each image builds successfully with `docker build`
- No `latest` tag used

**Spec reference**: NFR-025
**Plan reference**: Plan §6.3 (Docker Images table)

---

#### T-D002: ~~Create Minikube namespace manifests~~ [X] DONE

**Description**: Create namespace YAML files for todo-app, kafka, and monitoring namespaces.

**Preconditions**: None.

**Files to modify**:
- `k8s/local/namespaces/todo-app.yaml`
- `k8s/local/namespaces/kafka.yaml`
- `k8s/local/namespaces/monitoring.yaml`

**Expected output**:
- Three namespaces defined and ready for `kubectl apply`

**Spec reference**: Spec §17.1 (Minikube layout)
**Plan reference**: Plan §5.1 (Cluster Configuration)

---

#### T-D003: ~~Create local PostgreSQL Kubernetes manifests~~ [X] DONE

**Description**: Create Deployment, Service, PVC, and ConfigMap (with init.sql) for PostgreSQL in Minikube. Init script creates database and tables.

**Preconditions**: T-D002 complete (namespace exists).

**Files to modify**:
- `k8s/local/infrastructure/postgresql/deployment.yaml`
- `k8s/local/infrastructure/postgresql/service.yaml`
- `k8s/local/infrastructure/postgresql/pvc.yaml`
- `k8s/local/infrastructure/postgresql/configmap.yaml` — init.sql

**Expected output**:
- PostgreSQL pod runs in todo-app namespace
- PVC ensures data persists across pod restarts
- Init.sql creates `todo_app` database
- Service exposes port 5432

**Spec reference**: FR-051, Spec Clarification #4 (local PostgreSQL)
**Plan reference**: Plan §5.1 (Local Kubernetes Manifests: infrastructure/postgresql)

---

#### T-D004: ~~Create Strimzi Kafka Kubernetes manifests~~ [X] DONE

**Description**: Create Strimzi KafkaCluster CR and KafkaTopic CRs for all 8 topics in the kafka namespace.

**Preconditions**: T-D002 complete (kafka namespace exists).

**Files to modify**:
- `k8s/local/infrastructure/strimzi/kafka-cluster.yaml` — Strimzi KafkaCluster CR
- `k8s/local/infrastructure/strimzi/kafka-topics.yaml` — KafkaTopic CRs for all topics

**Expected output**:
- Strimzi KafkaCluster with 1 broker (Minikube resource constraints)
- 8 KafkaTopic CRs with correct partitions and retention per plan §3.1
- KRaft mode (no ZooKeeper) if Strimzi version supports it

**Spec reference**: Spec §8.2 (Kafka Topic Definitions)
**Plan reference**: Plan §3.1 (Kafka Topics), Plan §5.1 (infrastructure/strimzi), Plan §12 (Strimzi for local)

---

#### T-D005: ~~Create Kubernetes Secrets for local deployment~~ [X] DONE

**Description**: Create Secret manifests with base64-encoded values for local dev: db-secrets (DATABASE_URL), jwt-secrets (SECRET_KEY), openai-secrets (OPENAI_API_KEY).

**Preconditions**: T-D002 complete (namespace exists).

**Files to modify**:
- `k8s/local/secrets/db-secrets.yaml`
- `k8s/local/secrets/jwt-secrets.yaml`
- `k8s/local/secrets/openai-secrets.yaml`

**Expected output**:
- Secrets in todo-app namespace
- Values are placeholder base64 (user fills in real values)
- `.gitignore` updated to exclude actual secret values

**Spec reference**: FR-041, NFR-022
**Plan reference**: Plan §5.1 (Local Kubernetes Manifests: secrets/)

---

#### T-D006: ~~Create Kubernetes Deployment manifests for all services~~ [X] DONE

**Description**: Create Deployment + Service YAML for each of the 7 services with Dapr annotations (app-id, app-port, protocol, metrics).

**Preconditions**: T-D001 complete (Dockerfiles exist), T-D005 complete (secrets exist).

**Files to modify**:
- `k8s/local/services/task-api.yaml`
- `k8s/local/services/chat-api.yaml`
- `k8s/local/services/reminder-service.yaml`
- `k8s/local/services/recurring-service.yaml`
- `k8s/local/services/audit-service.yaml`
- `k8s/local/services/ws-sync-service.yaml`
- `k8s/local/services/frontend.yaml`

**Expected output**:
- Each file has Deployment + Service
- Dapr annotations per plan §5.1 (app-id, app-port, protocol, metrics)
- Environment variables reference Kubernetes secrets
- Liveness and readiness probes configured
- 1 replica each for local

**Spec reference**: FR-042, FR-045
**Plan reference**: Plan §5.1 (Dapr Annotations), Plan §1.1 (Ports/App IDs)

---

#### T-D007: ~~Create Minikube Ingress manifest~~ [X] DONE

**Description**: Create NGINX Ingress that routes `/` to frontend and `/ws/*` to ws-sync-service.

**Preconditions**: T-D006 complete (services exist).

**Files to modify**:
- `k8s/local/networking/ingress.yaml`

**Expected output**:
- NGINX Ingress controller routes
- `/` → frontend:3000
- `/ws/*` → ws-sync-service:8005 (WebSocket upgrade supported)
- Host-based or path-based routing

**Spec reference**: Spec §17.1 (Minikube Ingress)
**Plan reference**: Plan §5.1 (Ingress: NGINX)

---

#### T-D008: ~~Create Kustomization file for local deployment~~ [X] DONE

**Description**: Create `k8s/local/kustomization.yaml` that assembles all resources in correct order.

**Preconditions**: T-D002 through T-D007 complete.

**Files to modify**:
- `k8s/local/kustomization.yaml`

**Expected output**:
- Single `kubectl apply -k k8s/local/` deploys everything
- Resource ordering: namespaces → secrets → infrastructure → Dapr components → services → networking → monitoring

**Spec reference**: Spec §12 US7 (Minikube deployment via kustomize)
**Plan reference**: Plan §5.1 (Local Kubernetes Manifests)

---

#### T-D009: ~~Create Minikube setup script~~ [X] DONE

**Description**: Create `scripts/setup-minikube.sh` that starts Minikube, installs Dapr, installs Strimzi operator, enables ingress addon, builds images, and applies all manifests.

**Preconditions**: T-D008 complete (kustomization exists).

**Files to modify**:
- `scripts/setup-minikube.sh` — Full setup script
- `scripts/teardown-minikube.sh` — Cleanup script
- `scripts/port-forward.sh` — Port-forward for local access

**Expected output**:
- `bash scripts/setup-minikube.sh` brings up entire system from scratch
- Minikube started with 8GB RAM, 4 CPUs
- Dapr installed via `dapr init -k`
- Strimzi operator installed
- All images built via `minikube image build`
- All manifests applied
- Script waits for all pods to be Ready
- `scripts/teardown-minikube.sh` cleans everything up

**Spec reference**: SC-020 (deploy in under 5 minutes)
**Plan reference**: Plan §5.1, Plan §8 (scripts/)

---

## GROUP E — Cloud Deployment (AKS)

---

#### T-E001: ~~Create production namespace manifests~~ [X] DONE

**Description**: Create namespace YAML for todo-app and monitoring in production AKS cluster.

**Preconditions**: None.

**Files to modify**:
- `k8s/production/namespaces/todo-app.yaml`
- `k8s/production/namespaces/monitoring.yaml`

**Expected output**:
- Two namespaces for production use

**Spec reference**: Spec §17.2 (Production AKS)
**Plan reference**: Plan §5.2 (AKS Cluster Configuration)

---

#### T-E002: ~~Create production Kubernetes Deployment manifests~~ [X] DONE

**Description**: Create Deployment + Service YAML for all 7 services with Dapr annotations, resource limits/requests, and production-grade settings.

**Preconditions**: T-E001 complete (namespace exists).

**Files to modify**:
- `k8s/production/services/task-api.yaml`
- `k8s/production/services/chat-api.yaml`
- `k8s/production/services/reminder-service.yaml`
- `k8s/production/services/recurring-service.yaml`
- `k8s/production/services/audit-service.yaml`
- `k8s/production/services/ws-sync-service.yaml`
- `k8s/production/services/frontend.yaml`

**Expected output**:
- Resource limits/requests per plan §5.2 (Resource Limits table)
- Dapr annotations with mTLS enabled
- Image tags use `${SHA}` placeholder for CI/CD
- Secrets reference Azure Key Vault via Dapr secrets store
- Rolling update strategy

**Spec reference**: Spec §3.6 (Production K8s), NFR-025
**Plan reference**: Plan §5.2 (Resource Limits table)

---

#### T-E003: ~~Create HPA manifests for production~~ [X] DONE

**Description**: Create HorizontalPodAutoscaler resources for task-api, chat-api, frontend, and ws-sync-service.

**Preconditions**: T-E002 complete (deployments exist).

**Files to modify**:
- `k8s/production/autoscaling/task-api-hpa.yaml` — min:2, max:5, CPU:70%
- `k8s/production/autoscaling/chat-api-hpa.yaml` — min:1, max:3, CPU:70%
- `k8s/production/autoscaling/frontend-hpa.yaml` — min:2, max:4, CPU:70%
- `k8s/production/autoscaling/ws-sync-hpa.yaml` — min:1, max:3, CPU:70%

**Expected output**:
- HPA resources with correct min/max replicas and CPU target

**Spec reference**: Spec §3.6 (HPA), NFR-012
**Plan reference**: Plan §5.2 (autoscaling/)

---

#### T-E004: ~~Create PDB manifests for production~~ [X] DONE

**Description**: Create PodDisruptionBudget resources to ensure minimum availability during voluntary disruptions.

**Preconditions**: T-E002 complete (deployments exist).

**Files to modify**:
- `k8s/production/disruption/task-api-pdb.yaml` — minAvailable: 1
- `k8s/production/disruption/frontend-pdb.yaml` — minAvailable: 1
- `k8s/production/disruption/ws-sync-pdb.yaml` — minAvailable: 1

**Expected output**:
- PDB resources ensure at least 1 pod available during disruption

**Spec reference**: Spec §3.6 (Production-grade)
**Plan reference**: Plan §5.2 (disruption/)

---

#### T-E005: ~~Create production Ingress with TLS (cert-manager)~~ [X] DONE

**Description**: Create NGINX Ingress with TLS termination via cert-manager (Let's Encrypt). Create ClusterIssuer and Certificate resources.

**Preconditions**: T-E002 complete (services exist).

**Files to modify**:
- `k8s/production/networking/ingress.yaml` — TLS Ingress
- `k8s/production/networking/cert-manager/cluster-issuer.yaml` — Let's Encrypt issuer
- `k8s/production/networking/cert-manager/certificate.yaml` — TLS certificate

**Expected output**:
- HTTPS-only access to application
- cert-manager auto-provisions TLS certificates
- HTTP → HTTPS redirect
- `/ws/*` routes to ws-sync-service with WebSocket upgrade

**Spec reference**: Spec §3.6 (Ingress, TLS), Spec §12 US8.2 (TLS enforced)
**Plan reference**: Plan §5.2 (networking/)

---

#### T-E006: ~~Create Network Policies for production~~ [X] DONE

**Description**: Create Kubernetes NetworkPolicy resources to restrict inter-pod communication to only necessary paths.

**Preconditions**: T-E002 complete (services exist).

**Files to modify**:
- `k8s/production/networking/network-policies.yaml`

**Expected output**:
- Default deny all ingress/egress in todo-app namespace
- Allow rules per plan §5.2 (Network Policies section)
- frontend → task-api, chat-api
- task-api → postgresql (external), kafka
- reminder-service → kafka, task-api
- recurring-service → kafka, task-api
- audit-service → kafka, postgresql
- ws-sync-service → kafka

**Spec reference**: NFR-024
**Plan reference**: Plan §5.2 (Network Policies)

---

#### T-E007: ~~Create production Kustomization file~~ [X] DONE

**Description**: Create `k8s/production/kustomization.yaml` that assembles all production resources.

**Preconditions**: T-E001 through T-E006 complete.

**Files to modify**:
- `k8s/production/kustomization.yaml`

**Expected output**:
- Single `kubectl apply -k k8s/production/` deploys everything
- Proper resource ordering

**Spec reference**: Spec §17.2 (Production manifests)
**Plan reference**: Plan §5.2 (Production Kubernetes Manifests Structure)

---

## GROUP F — CI/CD

---

#### T-F001: ~~Create GitHub Actions CI workflow (PR gate)~~ [X] DONE

**Description**: Create `.github/workflows/ci.yaml` with jobs: lint-backend (ruff + mypy), lint-frontend (eslint + tsc), test-backend (pytest), test-frontend (vitest), docker-build-check.

**Preconditions**: Service source code exists.

**Files to modify**:
- `.github/workflows/ci.yaml`

**Expected output**:
- Triggers on PR to `main`
- 5 parallel jobs
- PR blocked if any check fails
- Uses `python:3.12` and `node:22` containers

**Spec reference**: Spec §12 US9.1 (PR gate), Spec §3.8 (CI/CD)
**Plan reference**: Plan §6.2 (Workflow 1: ci.yaml)

---

#### T-F002: ~~Create GitHub Actions CD workflow (build + push + deploy)~~ [X] DONE

**Description**: Create `.github/workflows/cd.yaml` with jobs: build-and-push (Docker images tagged with commit SHA → ghcr.io), deploy-staging (auto), deploy-production (manual approval gate).

**Preconditions**: T-D001 complete (Dockerfiles exist).

**Files to modify**:
- `.github/workflows/cd.yaml`

**Expected output**:
- Triggers on push to `main`
- Builds 7 Docker images, tags with `${{ github.sha }}`
- Pushes to ghcr.io
- Deploy-staging: auto after build
- Deploy-production: manual approval via GitHub Environments
- Uses `kustomize edit set image` to update tags
- `kubectl rollout status --timeout=120s` for verification

**Spec reference**: Spec §12 US9 (all acceptance scenarios), SC-021
**Plan reference**: Plan §6.2 (Workflow 2: cd.yaml)

---

## GROUP G — Monitoring & Logging

---

#### T-G001: ~~Implement structured JSON logging middleware~~ [X] DONE

**Description**: Create logging middleware for all Python services that outputs JSON with: timestamp, level, service, correlation_id, user_id, message, data. Create correlation ID middleware that generates/propagates `X-Correlation-ID` header.

**Preconditions**: None (middleware is independent).

**Files to modify**:
- `backend/app/middleware/correlation.py` — Correlation ID middleware
- `backend/app/middleware/logging.py` — Structured JSON logging middleware

**Expected output**:
- All log entries in JSON format per plan §7.4
- Correlation ID generated at entry if not present
- Correlation ID propagated to event envelopes
- User ID extracted from JWT and included in logs

**Spec reference**: NFR-026, Spec §12 US10.2
**Plan reference**: Plan §7.4 (Structured Logging, Correlation ID Propagation)

---

#### T-G002: ~~Implement Prometheus metrics middleware~~ [X] DONE

**Description**: Create metrics middleware using `prometheus_client` that exposes: `http_requests_total`, `http_request_duration_seconds`, `kafka_events_published_total`, `kafka_events_consumed_total`, `kafka_events_failed_total`, `tasks_created_total`, `tasks_completed_total`.

**Preconditions**: None (middleware is independent).

**Files to modify**:
- `backend/app/middleware/metrics.py` — Prometheus metrics middleware
- `backend/app/main.py` — Mount `/metrics` endpoint

**Expected output**:
- `GET /metrics` returns Prometheus text format
- All 10 custom metrics from plan §7.1 exposed
- Metrics include correct labels (method, endpoint, status_code, service, topic)

**Spec reference**: NFR-027, Spec §12 US10.1
**Plan reference**: Plan §7.1 (Custom Application Metrics table)

---

#### T-G003: ~~Implement health and readiness probes for all services~~ [X] DONE

**Description**: Ensure every service has `GET /api/health` (liveness) and `GET /api/ready` (readiness). Readiness checks: database connectivity (Task API, Audit Service), Kafka connectivity (all producers/consumers), Dapr sidecar availability.

**Preconditions**: Service scaffolds exist (T-A013, T-A016, T-A020, T-A023, T-A025).

**Files to modify**:
- `backend/app/routers/health.py` — Task API probes (check DB, Kafka, Dapr)
- `services/chat-api/app/routers/health.py` — Check Dapr
- `services/reminder/app/routers/health.py` — Check Kafka, Dapr
- `services/recurring/app/routers/health.py` — Check Kafka, Dapr
- `services/audit/app/routers/health.py` — Check DB, Kafka, Dapr
- `services/ws-sync/app/routers/health.py` — Check Kafka, Dapr

**Expected output**:
- Health: always returns `{"status": "healthy"}` if process is alive
- Ready: returns `{"status": "ready", "checks": {...}}` with component statuses
- Ready returns 503 if any critical dependency is down

**Spec reference**: Spec §11.3 (Health & Readiness), FR-045
**Plan reference**: Plan §2.1–2.6 (Probe Endpoints per service)

---

#### T-G004: ~~[P] Implement OpenTelemetry tracing instrumentation~~ [X] DONE

**Description**: Add OpenTelemetry SDK to all Python services. Instrument FastAPI, HTTP client calls, and Dapr operations. Configure OTLP exporter to send traces to OTel Collector.

**Preconditions**: None.

**Files to modify**:
- `backend/app/main.py` — OTel SDK init
- `backend/requirements.txt` — Add opentelemetry packages
- (Repeat for all 5 services in services/)

**Expected output**:
- Traces generated for all HTTP requests
- Trace context propagated via `traceparent` header
- Spans include: service name, endpoint, status code, duration
- Traces exported via OTLP to OTel Collector

**Spec reference**: NFR-028, Spec §12 US10.3
**Plan reference**: Plan §7.3 (OpenTelemetry)

---

#### T-G005: ~~Create Prometheus Kubernetes manifests and scrape config~~ [X] DONE

**Description**: Create Prometheus deployment, service, and ConfigMap with scrape configuration for all services and infrastructure.

**Preconditions**: T-D002 complete (monitoring namespace exists).

**Files to modify**:
- `k8s/local/monitoring/prometheus/deployment.yaml`
- `k8s/local/monitoring/prometheus/service.yaml`
- `k8s/local/monitoring/prometheus/configmap.yaml` — prometheus.yml scrape config
- `monitoring/prometheus/prometheus.yml` — Reference config

**Expected output**:
- Prometheus scrapes all service Dapr sidecars on port 9090 every 15s
- Scrapes Strimzi Kafka metrics on port 9404 every 30s
- Configuration matches plan §7.1 (Scrape Targets table)

**Spec reference**: NFR-027
**Plan reference**: Plan §7.1 (Prometheus Scrape Targets)

---

#### T-G006: ~~Create Grafana Kubernetes manifests and dashboard provisioning~~ [X] DONE

**Description**: Create Grafana deployment, service, and ConfigMap with 5 pre-provisioned dashboards: Service Overview, Kafka Overview, Task Metrics, Infrastructure, Dapr.

**Preconditions**: T-G005 complete (Prometheus deployed).

**Files to modify**:
- `k8s/local/monitoring/grafana/deployment.yaml`
- `k8s/local/monitoring/grafana/service.yaml`
- `k8s/local/monitoring/grafana/configmap.yaml` — Dashboard provisioning
- `monitoring/grafana/dashboards/service-overview.json`
- `monitoring/grafana/dashboards/kafka-overview.json`
- `monitoring/grafana/dashboards/task-metrics.json`
- `monitoring/grafana/dashboards/infrastructure.json`

**Expected output**:
- Grafana accessible on NodePort or Ingress
- Prometheus configured as data source
- 5 dashboards auto-provisioned per plan §7.2
- Service Overview: request rate, error rate, p50/p95/p99 latency
- Kafka Overview: consumer lag, messages/sec

**Spec reference**: NFR-029, Spec §12 US10.1
**Plan reference**: Plan §7.2 (Grafana Dashboards table)

---

#### T-G007: ~~[P] Create OpenTelemetry Collector Kubernetes manifests~~ [X] DONE

**Description**: Create OTel Collector deployment, service, and ConfigMap with pipeline configuration: receive OTLP → export to Prometheus (metrics) and Grafana Tempo/stdout (traces).

**Preconditions**: T-D002 complete (monitoring namespace exists).

**Files to modify**:
- `k8s/local/monitoring/otel-collector/deployment.yaml`
- `k8s/local/monitoring/otel-collector/service.yaml`
- `k8s/local/monitoring/otel-collector/configmap.yaml`
- `monitoring/otel/otel-collector-config.yaml` — Reference config

**Expected output**:
- OTel Collector receives traces via OTLP gRPC (port 4317)
- Exports metrics to Prometheus
- Exports traces to stdout (local) or Tempo (production)
- Pipeline per plan §7.3

**Spec reference**: NFR-028
**Plan reference**: Plan §7.3 (Collector Pipeline)

---

## Dependencies & Execution Order

### Phase Dependencies (Critical Path)

```
T-A001 ─→ T-A002 ─→ T-A004 (migration)
  │          │
  │          └─→ T-A005 ─→ T-A006 ─→ T-A007 ─→ T-A008 ─→ T-A010
  │                                      │          │
  │                                      │          └─→ T-A012
  │                                      └─→ T-A009
  │                                      └─→ T-A011
  │
  └─→ T-B001 ─→ T-B002 ─→ T-B003 (event publishing in Task API)
         │                    │
         └─→ T-B004          └─→ T-A015 (recurring handler needs events)
                                  └─→ T-A017 (reminder handler needs events)
                                  └─→ T-A021 (audit handler needs events)
                                  └─→ T-A024 (ws-sync handler needs events)
```

### Parallel Opportunities

**Can run in parallel from the start (no dependencies)**:
- T-A003, T-A013, T-A016, T-A020, T-A023, T-A025 (service scaffolds)
- T-B001 (event schemas)
- T-C001, T-C002, T-C003, T-C004, T-C005, T-C006 (Dapr components)
- T-D002 (namespaces)
- T-G001, T-G002 (middleware)

**Can run in parallel after data model (T-A001, T-A002)**:
- T-A005 (tag CRUD) || T-A009 (search) || T-A011 (sort)
- T-A027, T-A028, T-A029, T-A030 (frontend — parallel with each other)

**Can run in parallel after event schemas (T-B001)**:
- T-B004 (copy schemas to all services)

**Independent groups that can proceed in parallel**:
- GROUP C (Dapr components) — fully independent
- GROUP D (Minikube manifests) — depends only on Dockerfiles
- GROUP E (AKS manifests) — depends only on Dockerfiles
- GROUP F (CI/CD) — depends on Dockerfiles and source code
- GROUP G (Monitoring) — mostly independent

### Recommended Execution Order

```
WAVE 1 (parallel):
  T-A001, T-A003, T-B001, T-C001–C006, T-D002, T-G001, T-G002

WAVE 2 (after Wave 1):
  T-A002, T-A004, T-A013, T-A016, T-A020, T-A023, T-A025, T-B002

WAVE 3 (after Wave 2):
  T-A005, T-A006, T-A007, T-B003, T-B004, T-A014, T-A017
  T-D001 (Dockerfiles — needs service scaffolds)

WAVE 4 (after Wave 3):
  T-A008, T-A009, T-A010, T-A011, T-A012
  T-A015, T-A018, T-A019, T-A021, T-A022, T-A024
  T-A026, T-A027, T-A028, T-A029, T-A030, T-A031

WAVE 5 (after Wave 4):
  T-D003–D009 (Minikube deployment)
  T-E001–E007 (AKS deployment)
  T-F001–F002 (CI/CD)
  T-G003–G007 (Monitoring deployment)
```

---

## Task Summary

| Group | Count | Description |
|-------|-------|-------------|
| A — Advanced Features | 31 | Data models, CRUD, services, frontend |
| B — Kafka Integration | 4 | Event schemas, publisher, wiring |
| C — Dapr Integration | 6 | Pub/Sub, state, secrets, subscriptions |
| D — Local Deployment | 9 | Dockerfiles, K8s manifests, Minikube setup |
| E — Cloud Deployment | 7 | AKS manifests, HPA, PDB, TLS, network policies |
| F — CI/CD | 2 | GitHub Actions workflows |
| G — Monitoring & Logging | 7 | Logging, metrics, probes, OTel, Prometheus, Grafana |
| **Total** | **66** | |

---

## Notes

- All tasks are implementation-only — no tasks produce spec or plan artifacts
- Every task references its source spec section and plan section for traceability
- [P] tasks can run in parallel with other [P] tasks in the same wave
- Service scaffolds include middleware from the start (no separate middleware tasks)
- Event schemas are duplicated per service (plan decision: no shared library)
- Frontend tasks (T-A027–T-A031) can all proceed in parallel after T-A027
