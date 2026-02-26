# Feature Specification: Phase V — Advanced Event-Driven Cloud Deployment

**Feature Branch**: `003-event-driven-cloud`
**Created**: 2026-02-22
**Status**: Draft (Clarified)
**Input**: Evolve the Todo full-stack application into an event-driven, cloud-native system with advanced task features (recurring tasks, due dates, scheduled reminders), intermediate features (priorities, tags, search, filter, sort), Kafka-based event streaming, Dapr runtime integration, Kubernetes deployment (Minikube + production AKS/GKE/OKE), managed Kafka (Redpanda Cloud), CI/CD via GitHub Actions, and production-grade monitoring and logging.

---

## 1. Context & Phase

This is Phase V of the Todo application. Phases I–IV delivered:
- **Phase I**: Console-based Todo app
- **Phase II**: Full-stack web app (Next.js + FastAPI + Neon PostgreSQL + JWT auth)
- **Phase III**: AI Chatbot interface (OpenAI Agents SDK + MCP tools + ChatKit UI)
- **Phase IV**: Consolidation and refinement

Phase V introduces **event-driven architecture**, **cloud-native deployment**, and **advanced task management features**. The system evolves from a monolithic request-response model to a decoupled, event-driven architecture using Apache Kafka (Redpanda Cloud) and Dapr as the runtime abstraction layer. The application is containerized and deployed to Kubernetes — first locally via Minikube, then to a production-grade managed Kubernetes cluster.

**Phase**: V — Advanced Event-Driven Cloud Deployment

---

## Clarifications

### Session 2026-02-22

1. **Q: How should recurring tasks be triggered — cron-based (Dapr Jobs fires on schedule) or completion-based (next instance generated when current is completed)?**
   → **A: Completion-based.** Next instance is generated ONLY when the user completes the current one. Prevents pile-up of uncompleted tasks. Dapr Jobs API is NOT used for recurrence triggering. The Recurring Task Service listens for `task.completed` events and generates the next instance if the task has recurrence fields.

2. **Q: Which production Kubernetes provider should we target?**
   → **A: AKS (Azure Kubernetes Service).** Azure Key Vault for secrets management. Dapr has strong Azure integration (born at Microsoft). Generous free tier ($200 credits).

3. **Q: How should the frontend talk to the Task API in Kubernetes?**
   → **A: SSR Proxy pattern.** Browser → Next.js Server (via Ingress) → Dapr Sidecar → Task API. All API calls are server-side via Next.js Route Handlers. Browser never calls FastAPI directly. This replaces the Phase II/III pattern of direct browser-to-backend calls.

4. **Q: Should Minikube use a local PostgreSQL container or connect to Neon cloud?**
   → **A: Local PostgreSQL.** Run PostgreSQL in a Minikube pod. Fully self-contained, works offline, clean data per dev session. Neon is used only in production.

5. **Q: How should `is_overdue` be computed — stored boolean or query-time?**
   → **A: Query-time computed.** Calculate `due_date < now() AND status != completed` at query time. Always accurate, no stale data. Remove `is_overdue` as a stored column; make it a computed field in the API response.

6. **Q: Can a task have multiple reminders?**
   → **A: Single reminder per task.** One `reminder_at` field on the Task entity. Users can update the reminder time. Covers 90% of use cases.

7. **Q: Can users rename or recolor existing tags?**
   → **A: Yes, add `PATCH /api/tags/{tag_id}`.** Allow renaming (updates slug) and recoloring. Better UX when a tag is used on many tasks.

8. **Q: Should there be limits on tags?**
   → **A: Yes — max 50 tags per user, max 10 tags per task.** Prevents abuse and keeps UI clean.

9. **Q: Which service writes to the AuditLog table?**
   → **A: Task API self-consumes.** Task API subscribes to `todo.audit.log` and writes to AuditLog table. No dedicated Audit Service needed.

10. **Q: Since recurrence is completion-based (no cron jobs), should Dapr Jobs still be used for reminders?**
    → **A: Yes, use Dapr Jobs API for reminders.** Schedule a one-time Dapr Job at `reminder_at` time. When it fires, the Reminder Service publishes `reminder.triggered`. Demonstrates Dapr Jobs building block.

11. **Q: Which PostgreSQL text search configuration for full-text search?**
    → **A: `english` configuration** with stemming (e.g., "running" matches "run"). Better results for English-only users.

12. **Q: Should the Phase III AI Chatbot's MCP tools be updated for new features?**
    → **A: Yes, update MCP tools.** Extend existing tools (add_task, list_tasks, etc.) with new fields (due_date, tags, reminder_at, search, filter). Full feature parity between dashboard and chatbot.

---

## 2. Purpose

Enable users to manage tasks with advanced capabilities (recurring schedules, due dates, scheduled reminders, tags, search, filter, sort) while the system operates on a decoupled, event-driven architecture that scales horizontally, tolerates faults gracefully, and deploys to production Kubernetes with full CI/CD, monitoring, and logging.

---

## 3. Objectives

### 3.1 Advanced Task Features
- **Recurring Tasks**: Tasks that auto-regenerate when completed (completion-based trigger, NOT cron-based). Patterns: daily, weekly, monthly, custom interval.
- **Due Dates**: Tasks with optional deadline timestamps; overdue detection (query-time computed)
- **Scheduled Reminders**: One-time reminders triggered via Dapr Jobs API at the specified `reminder_at` time (single reminder per task)

### 3.2 Intermediate Task Features
- **Priorities**: Already exists (low, medium, high) — add `critical` level and priority-based sorting
- **Tags**: User-defined labels for categorization (many-to-many relationship)
- **Search**: Full-text search across task title and description
- **Filter**: Filter tasks by status, priority, tags, due date range, overdue
- **Sort**: Sort tasks by created_at, due_date, priority, title

### 3.3 Event-Driven Architecture
- Introduce Apache Kafka as the event backbone
- All state-changing operations emit domain events
- Consumers process events asynchronously for side effects (reminders, recurring task generation, audit logging)

### 3.4 Dapr Integration
- **Pub/Sub**: Kafka-backed publish/subscribe for domain events
- **State Management**: Distributed state store for caching and session data
- **Jobs API**: Schedule and trigger recurring tasks and reminders
- **Secrets Management**: Externalize all secrets (DB credentials, JWT secret, API keys)
- **Service Invocation**: Service-to-service calls via Dapr sidecar (replaces direct HTTP)

### 3.5 Local Deployment (Minikube)
- All services containerized (Docker)
- Helm charts or Kubernetes manifests for local deployment
- Dapr sidecar injection in Minikube

### 3.6 Production Kubernetes Deployment (AKS)
- Deploy to Azure Kubernetes Service (AKS)
- Azure Key Vault for Dapr Secrets Management
- Production-grade networking (Ingress, TLS)
- Horizontal Pod Autoscaler (HPA)
- Resource limits and requests

### 3.7 Managed Kafka (Redpanda Cloud)
- Redpanda Cloud as the managed Kafka-compatible streaming platform
- Topic provisioning and schema management
- mTLS or SASL authentication

### 3.8 CI/CD (GitHub Actions)
- Build, test, lint pipeline on every PR
- Container image build and push to registry
- Automated deployment to staging and production Kubernetes

### 3.9 Monitoring & Logging
- Structured JSON logging across all services
- Metrics collection (Prometheus)
- Dashboards (Grafana)
- Distributed tracing (OpenTelemetry)
- Health checks and readiness probes

---

## 4. In-Scope

- Recurring task creation, scheduling, and auto-generation
- Due date assignment and overdue detection
- Scheduled reminders via Dapr Jobs API
- Tags CRUD and task-tag association
- Full-text search (PostgreSQL `tsvector` or application-level)
- Multi-criteria filtering (status, priority, tags, due date, overdue)
- Multi-field sorting (created_at, due_date, priority, title)
- Critical priority level addition
- Kafka topic design and event schema definitions
- Dapr component configuration (pub/sub, state, jobs, secrets, service invocation)
- Dockerfiles for frontend and backend
- Kubernetes manifests / Helm charts
- Minikube local deployment scripts
- Production Kubernetes deployment (AKS — Azure)
- Redpanda Cloud cluster provisioning and configuration
- GitHub Actions CI/CD pipeline
- Prometheus + Grafana monitoring stack
- OpenTelemetry distributed tracing
- Structured logging with correlation IDs
- Health and readiness endpoints

## 5. Out-of-Scope

- Real-time push notifications (WebSocket/SSE) — events are processed server-side only
- Email/SMS delivery for reminders (log-only in this phase)
- Multi-tenancy / organization-level features
- Task sharing between users
- File attachments
- OAuth / social login
- GraphQL API
- Service mesh (Istio/Linkerd) — Dapr handles service communication
- Multi-region deployment
- Cost optimization / FinOps
- Load testing / performance benchmarking (deferred to Phase VI)

---

## 6. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js 16+ (App Router, TypeScript, Tailwind CSS) | Extended with filter/search/sort UI |
| Backend API | Python FastAPI | Event-producing microservice |
| Reminder Service | Python FastAPI (new microservice) | Consumes reminder events, manages schedules |
| Recurring Task Service | Python FastAPI (new microservice) | Generates recurring task instances |
| ORM | SQLModel | Extended models for due dates, tags, recurrence |
| Database | PostgreSQL (Neon Serverless) | Full-text search via tsvector |
| Event Streaming | Apache Kafka (Redpanda Cloud) | Managed, Kafka-compatible |
| Runtime | Dapr | Pub/Sub, State, Jobs, Secrets, Service Invocation |
| Container Runtime | Docker | Multi-stage builds |
| Orchestration (Local) | Minikube | Local Kubernetes cluster |
| Orchestration (Prod) | AKS (Azure) | Managed Kubernetes |
| CI/CD | GitHub Actions | Build → Test → Push → Deploy |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Tracing | OpenTelemetry | Distributed traces |
| Logging | Structured JSON (Python logging) | With correlation IDs |
| Container Registry | GitHub Container Registry (ghcr.io) | Or Docker Hub |
| Secrets | Dapr Secrets Management | Backed by Kubernetes secrets or cloud vault |

---

## 7. Architecture Overview

### 7.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER                           │
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐                       │
│  │   Frontend        │    │   Ingress         │                      │
│  │   (Next.js)       │◄───│   Controller      │◄──── Users           │
│  │   + Dapr Sidecar  │    │   (TLS)           │                      │
│  └────────┬─────────┘    └──────────────────┘                       │
│           │ Dapr Service Invocation                                  │
│           ▼                                                          │
│  ┌──────────────────┐         ┌──────────────────────┐              │
│  │   Task API        │────────►│   Kafka (Redpanda)    │              │
│  │   (FastAPI)       │ publish │                       │              │
│  │   + Dapr Sidecar  │        │   Topics:              │              │
│  └────────┬─────────┘        │   • task.created        │              │
│           │                   │   • task.updated        │              │
│           │                   │   • task.deleted        │              │
│           │                   │   • task.completed      │              │
│           │                   │   • reminder.scheduled   │              │
│           │                   │   • reminder.triggered   │              │
│           │                   │   • recurring.due        │              │
│           │                   └───────┬──────┬─────────┘              │
│           │                           │      │                        │
│           │                    ┌──────▼──┐ ┌─▼────────────┐          │
│           │                    │Reminder │ │Recurring Task │          │
│           │                    │Service  │ │Service        │          │
│           │                    │+Dapr    │ │+Dapr          │          │
│           │                    └─────────┘ └───────────────┘          │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐    ┌──────────────────┐                       │
│  │   PostgreSQL      │    │   Dapr State      │                      │
│  │   (Neon)          │    │   Store (Redis)    │                      │
│  └──────────────────┘    └──────────────────┘                       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │   Observability Stack                                      │       │
│  │   Prometheus │ Grafana │ OpenTelemetry Collector            │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Service Decomposition

| Service | Responsibility | Dapr Building Blocks Used |
|---------|---------------|--------------------------|
| **Task API** | Task CRUD, event publishing, search/filter/sort, audit log self-consumption | Pub/Sub (publish + subscribe for audit), Secrets, Service Invocation |
| **Reminder Service** | Consume `reminder.scheduled` events, schedule Dapr Jobs, fire reminders | Pub/Sub (subscribe), Jobs API, State Management |
| **Recurring Task Service** | Consume `task.completed` events, generate next recurring instance | Pub/Sub (subscribe), Service Invocation (call Task API to create next instance) |
| **Frontend** | UI for task management, search, filter, sort | Service Invocation (Next.js SSR → Dapr sidecar → Task API) |

---

## 8. Event-Driven Architecture

### 8.1 Domain Events

Every state-changing operation on a task produces a domain event published to Kafka via Dapr Pub/Sub.

| Event | Trigger | Producer | Consumers |
|-------|---------|----------|-----------|
| `task.created` | New task created | Task API | Audit Log consumer (Task API self-consumes) |
| `task.updated` | Task fields modified | Task API | Reminder Service (if due_date/reminder_at changed), Audit Log |
| `task.completed` | Task marked completed | Task API | Recurring Task Service (generate next instance if recurring), Audit Log |
| `task.deleted` | Task deleted | Task API | Reminder Service (cancel pending Dapr Job), Audit Log |
| `reminder.scheduled` | Reminder time set/changed | Task API | Reminder Service (schedule Dapr Job) |
| `reminder.triggered` | Dapr Job fires at reminder_at | Reminder Service | Task API (set reminder_sent=true) |

### 8.2 Kafka Topic Definitions

| Topic Name | Partitions | Retention | Key | Description |
|-----------|-----------|-----------|-----|-------------|
| `todo.task.created` | 3 | 7 days | `user_id` | Emitted when a task is created |
| `todo.task.updated` | 3 | 7 days | `user_id` | Emitted when task fields are modified |
| `todo.task.completed` | 3 | 7 days | `user_id` | Emitted when task status → completed |
| `todo.task.deleted` | 3 | 7 days | `user_id` | Emitted when a task is deleted |
| `todo.reminder.scheduled` | 3 | 7 days | `task_id` | Emitted when a reminder is set/changed |
| `todo.reminder.triggered` | 3 | 3 days | `task_id` | Emitted when a reminder fires |
| `todo.audit.log` | 6 | 30 days | `user_id` | All events replayed for audit trail |

**Note**: `todo.recurring.due` topic removed — recurrence is completion-based (triggered by `task.completed` event), not cron-based.

**Partitioning Strategy**: Key by `user_id` for task events ensures ordering per user. Key by `task_id` for reminder/recurring events ensures ordering per task.

### 8.3 Event Schemas

All events follow a common envelope:

```json
{
  "event_id": "uuid-v4",
  "event_type": "task.created",
  "event_version": "1.0",
  "timestamp": "2026-02-22T10:30:00Z",
  "source": "task-api",
  "correlation_id": "uuid-v4",
  "user_id": "uuid-v4",
  "data": { }
}
```

#### `task.created` Event Data

```json
{
  "task_id": "uuid",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending",
  "priority": "high",
  "due_date": "2026-02-25T09:00:00Z",
  "tags": ["shopping", "personal"],
  "recurrence": {
    "pattern": "weekly",
    "interval": 1,
    "ends_at": "2026-06-01T00:00:00Z"
  }
}
```

#### `task.updated` Event Data

```json
{
  "task_id": "uuid",
  "changes": {
    "title": { "old": "Buy groceries", "new": "Buy organic groceries" },
    "priority": { "old": "medium", "new": "high" },
    "due_date": { "old": null, "new": "2026-02-25T09:00:00Z" }
  }
}
```

#### `task.completed` Event Data

```json
{
  "task_id": "uuid",
  "title": "Buy groceries",
  "completed_at": "2026-02-22T14:00:00Z",
  "has_recurrence": true,
  "recurrence_pattern": "weekly",
  "recurrence_interval": 1,
  "recurrence_ends_at": "2026-06-01T00:00:00Z",
  "current_due_date": "2026-02-22T09:00:00Z"
}
```

#### `task.deleted` Event Data

```json
{
  "task_id": "uuid",
  "title": "Buy groceries",
  "had_reminders": true,
  "had_recurrence": false
}
```

#### `reminder.scheduled` Event Data

```json
{
  "task_id": "uuid",
  "reminder_id": "uuid",
  "remind_at": "2026-02-25T08:00:00Z",
  "task_title": "Buy groceries",
  "task_due_date": "2026-02-25T09:00:00Z"
}
```

#### `reminder.triggered` Event Data

```json
{
  "task_id": "uuid",
  "reminder_id": "uuid",
  "triggered_at": "2026-02-25T08:00:00Z",
  "task_title": "Buy groceries",
  "action": "log"
}
```

**Note**: The `recurring.due` event has been removed. Recurrence is now completion-based: when a recurring task is completed, the Recurring Task Service consumes the `task.completed` event and creates the next instance via Dapr Service Invocation to the Task API.

---

## 9. Dapr Building Blocks Mapping

### 9.1 Pub/Sub (Kafka via Redpanda Cloud)

**Component**: `pubsub-kafka`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub-kafka
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      secretKeyRef:
        name: kafka-secrets
        key: brokers
    - name: authType
      value: "password"
    - name: saslUsername
      secretKeyRef:
        name: kafka-secrets
        key: username
    - name: saslPassword
      secretKeyRef:
        name: kafka-secrets
        key: password
    - name: saslMechanism
      value: "SCRAM-SHA-256"
    - name: initialOffset
      value: "oldest"
    - name: maxMessageBytes
      value: "1048576"
```

**Usage**:
- Task API publishes to `todo.task.*` and `todo.reminder.scheduled` topics
- Reminder Service subscribes to `todo.reminder.scheduled` and `todo.task.deleted`
- Recurring Task Service subscribes to `todo.task.completed` and `todo.recurring.due`

### 9.2 State Management (Redis)

**Component**: `statestore-redis`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore-redis
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: "redis:6379"
    - name: redisPassword
      secretKeyRef:
        name: redis-secrets
        key: password
    - name: actorStateStore
      value: "true"
```

**Usage**:
- Cache frequently accessed task lists per user
- Store reminder job state (scheduled, triggered, cancelled)
- Store recurring task schedule metadata

### 9.3 Jobs API (Scheduled Reminders Only)

**Usage**:
- When a task with `reminder_at` is created/updated, the Reminder Service schedules a one-time Dapr Job at the `reminder_at` time
- When the Dapr Job fires, the Reminder Service publishes a `reminder.triggered` event
- If the task is deleted or the reminder time changes, the existing job is cancelled and (if applicable) a new one is scheduled
- **Note**: Dapr Jobs is NOT used for recurring task generation — recurrence is completion-based (driven by `task.completed` events)

**Job Schedule Example**:
```json
{
  "name": "reminder-{task_id}",
  "dueTime": "2026-02-25T08:00:00Z",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "task_title": "Buy groceries",
    "action": "trigger_reminder"
  }
}
```

### 9.4 Secrets Management

**Component**: `secrets-kubernetes` (Minikube) / `secrets-azure-keyvault` (AKS production)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: secrets-store
spec:
  type: secretstores.kubernetes
  version: v1
```

**Managed Secrets**:
| Secret Name | Contents |
|------------|----------|
| `db-secrets` | `DATABASE_URL` |
| `jwt-secrets` | `SECRET_KEY` |
| `kafka-secrets` | `brokers`, `username`, `password` |
| `redis-secrets` | `password` |
| `openai-secrets` | `OPENAI_API_KEY` |

### 9.5 Service Invocation

**Usage**:
- Frontend → Task API: All task operations via Dapr service invocation (replaces direct HTTP in Kubernetes)
- Recurring Task Service → Task API: Create new task instance when recurring schedule fires
- Reminder Service → Task API: Update task metadata when reminder triggers

**Invocation Pattern**:
```
# Instead of: http://task-api:8000/api/tasks
# Use: http://localhost:3500/v1.0/invoke/task-api/method/api/tasks
```

---

## 10. Data Model Extensions

### 10.1 Extended Task Entity

| Field | Type | Constraints | Notes | New? |
|-------|------|-------------|-------|------|
| id | string (UUID) | PK | Server-generated | Existing |
| title | string | NOT NULL, max 255 | Required | Existing |
| description | string | NULLABLE, max 2000 | Optional | Existing |
| status | string | NOT NULL, default: "pending" | pending, in_progress, completed | Existing |
| priority | string | NOT NULL, default: "medium" | low, medium, high, **critical** | **Extended** |
| user_id | string (UUID) | NOT NULL, INDEX | Owner reference | Existing |
| **due_date** | datetime | NULLABLE | Optional deadline | **New** |
| ~~is_overdue~~ | — | — | **NOT STORED** — computed at query time: `due_date < now() AND status != completed`. Appears in API response only. | **Computed** |
| **recurrence_pattern** | string | NULLABLE | daily, weekly, monthly | **New** |
| **recurrence_interval** | integer | NULLABLE, default: 1 | e.g., every 2 weeks (pattern=weekly, interval=2) | **New** |
| **recurrence_ends_at** | datetime | NULLABLE | When recurrence stops | **New** |
| **source_task_id** | string (UUID) | NULLABLE, INDEX | Parent recurring task reference | **New** |
| **reminder_at** | datetime | NULLABLE | When to send reminder | **New** |
| **reminder_sent** | boolean | NOT NULL, default: false | Whether reminder was triggered | **New** |
| **search_vector** | tsvector | INDEX (GIN) | Full-text search index | **New** |
| created_at | datetime | NOT NULL | Auto-set | Existing |
| updated_at | datetime | NOT NULL | Auto-set | Existing |

### 10.2 New: Tag Entity

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | string (UUID) | PK | Server-generated |
| name | string | NOT NULL, max 50 | Tag display name |
| slug | string | NOT NULL, UNIQUE per user | Lowercase, normalized |
| color | string | NULLABLE, max 7 | Hex color code (#FF5733) |
| user_id | string (UUID) | NOT NULL, INDEX | Owner reference |
| created_at | datetime | NOT NULL | Auto-set |

**Unique constraint**: `(slug, user_id)` — each user has unique tag slugs.

### 10.3 New: TaskTag Junction Entity

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| task_id | string (UUID) | PK, FK → Task | Task reference |
| tag_id | string (UUID) | PK, FK → Tag | Tag reference |

### 10.4 New: AuditLog Entity

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | string (UUID) | PK | Server-generated |
| event_type | string | NOT NULL | Domain event type |
| event_data | JSON | NOT NULL | Full event payload |
| user_id | string (UUID) | NOT NULL, INDEX | Who triggered it |
| correlation_id | string (UUID) | NOT NULL, INDEX | Request trace ID |
| created_at | datetime | NOT NULL | Event timestamp |

### 10.5 Entity Relationships

```
User (1) ──── (*) Task
User (1) ──── (*) Tag
Task (*) ──── (*) Tag  (via TaskTag)
Task (1) ──── (*) Task (source_task_id → self-referential for recurring)
Task (1) ──── (*) AuditLog (via user_id + task events)
User (1) ──── (*) Conversation (Phase III, unchanged)
Conversation (1) ──── (*) Message (Phase III, unchanged)
```

### 10.6 Indexes

| Index | Table | Columns | Type | Purpose |
|-------|-------|---------|------|---------|
| `ix_task_user_id` | Task | user_id | B-tree | Filter by user |
| `ix_task_due_date` | Task | due_date | B-tree | Sort/filter by due date |
| `ix_task_search` | Task | search_vector | GIN | Full-text search |
| `ix_task_source_task_id` | Task | source_task_id | B-tree | Find recurring instances |
| `ix_tag_user_id` | Tag | user_id | B-tree | Filter tags by user |
| `ix_tag_slug_user` | Tag | (slug, user_id) | B-tree UNIQUE | Unique tags per user |
| `ix_audit_user_id` | AuditLog | user_id | B-tree | User audit trail |
| `ix_audit_correlation` | AuditLog | correlation_id | B-tree | Trace correlation |

---

## 11. API Contracts (Extended)

### 11.1 Existing Endpoints (Modified)

#### `GET /api/tasks` — Enhanced with Search, Filter, Sort

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: pending, in_progress, completed |
| `priority` | string | Filter: low, medium, high, critical |
| `tag` | string | Filter by tag slug (repeatable for multiple tags) |
| `due_before` | datetime | Filter: due date before this timestamp |
| `due_after` | datetime | Filter: due date after this timestamp |
| `overdue` | boolean | Filter: only overdue tasks (true/false) |
| `search` | string | Full-text search query across title and description |
| `sort_by` | string | Sort field: created_at, due_date, priority, title (default: created_at) |
| `sort_order` | string | asc or desc (default: desc) |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 20, max: 100) |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Buy groceries",
      "description": "Milk, eggs",
      "status": "pending",
      "priority": "high",
      "due_date": "2026-02-25T09:00:00Z",
      "is_overdue": false,
      "recurrence_pattern": "weekly",
      "reminder_at": "2026-02-25T08:00:00Z",
      "reminder_sent": false,
      "tags": [
        { "id": "uuid", "name": "Shopping", "slug": "shopping", "color": "#FF5733" }
      ],
      "user_id": "uuid",
      "created_at": "2026-02-22T10:00:00Z",
      "updated_at": "2026-02-22T10:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

#### `POST /api/tasks` — Enhanced with New Fields

**Request Body** (extended):
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending",
  "priority": "high",
  "due_date": "2026-02-25T09:00:00Z",
  "reminder_at": "2026-02-25T08:00:00Z",
  "recurrence_pattern": "weekly",
  "recurrence_interval": 1,
  "recurrence_ends_at": "2026-06-01T00:00:00Z",
  "tag_ids": ["uuid-1", "uuid-2"]
}
```

| Field | Required | Default | Constraints |
|-------|----------|---------|-------------|
| title | Yes | — | Non-empty, max 255 |
| description | No | null | Max 2000 |
| status | No | "pending" | pending, in_progress, completed |
| priority | No | "medium" | low, medium, high, critical |
| due_date | No | null | ISO 8601 datetime, must be in future |
| reminder_at | No | null | ISO 8601 datetime, must be before due_date |
| recurrence_pattern | No | null | daily, weekly, monthly |
| recurrence_interval | No | 1 | Positive integer (e.g., 2 = every 2 weeks if pattern=weekly) |
| recurrence_ends_at | No | null | ISO 8601, must be after due_date |
| tag_ids | No | [] | Array of existing tag UUIDs (max 10 per task) |

**Events Emitted**: `task.created`, `reminder.scheduled` (if reminder_at set)

### 11.2 New Endpoints

#### `GET /api/tags` — List User Tags

**Response** `200 OK`:
```json
[
  { "id": "uuid", "name": "Shopping", "slug": "shopping", "color": "#FF5733", "task_count": 5 },
  { "id": "uuid", "name": "Work", "slug": "work", "color": "#3498DB", "task_count": 12 }
]
```

#### `POST /api/tags` — Create Tag

**Request Body**:
```json
{
  "name": "Shopping",
  "color": "#FF5733"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "name": "Shopping",
  "slug": "shopping",
  "color": "#FF5733",
  "user_id": "uuid",
  "created_at": "2026-02-22T10:00:00Z"
}
```

#### `PATCH /api/tags/{tag_id}` — Update Tag

**Request Body** (all fields optional):
```json
{
  "name": "Updated Name",
  "color": "#00FF00"
}
```

Renaming a tag also updates its slug. Returns 409 if the new name conflicts with an existing tag for the same user.

**Response** `200 OK`: Updated tag object.

#### `DELETE /api/tags/{tag_id}` — Delete Tag

Removes tag and all task-tag associations. Does not delete tasks.

**Response** `204 No Content`

#### `POST /api/tasks/{task_id}/tags` — Add Tags to Task

**Request Body**:
```json
{
  "tag_ids": ["uuid-1", "uuid-2"]
}
```

**Response** `200 OK`: Updated task with tags.

#### `DELETE /api/tasks/{task_id}/tags/{tag_id}` — Remove Tag from Task

**Response** `204 No Content`

#### `GET /api/tasks/overdue` — List Overdue Tasks

Returns tasks where `due_date < now()` AND `status != completed`.

**Response** `200 OK`: Same paginated format as `GET /api/tasks`.

### 11.3 Health & Readiness Endpoints

#### `GET /api/health` — Liveness Probe

```json
{ "status": "healthy" }
```

#### `GET /api/ready` — Readiness Probe

```json
{
  "status": "ready",
  "checks": {
    "database": "connected",
    "kafka": "connected",
    "dapr": "available"
  }
}
```

---

## 12. User Scenarios & Testing

### User Story 1 — Create Task with Due Date and Reminder (Priority: P1)

An authenticated user creates a task with a deadline and a scheduled reminder.

**Why this priority**: Due dates and reminders are the most impactful advanced features. They transform the app from a simple list into a time-aware productivity tool.

**Independent Test**: Sign in, create a task with due_date and reminder_at, verify task appears with due date badge. Verify reminder event is scheduled in Dapr Jobs.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they create a task with title "Submit report" and due_date "2026-03-01T17:00:00Z" and reminder_at "2026-03-01T09:00:00Z", **Then** the task is created with the due date and reminder fields set, and a `task.created` event is published to Kafka, and a `reminder.scheduled` event is published.
2. **Given** a task with a due date in the past and status != completed, **When** the user views their task list, **Then** the task is flagged as `is_overdue: true`.
3. **Given** a task with reminder_at set, **When** the reminder time is reached, **Then** the Dapr Jobs API fires a `reminder.triggered` event and the task's `reminder_sent` field is set to true.
4. **Given** an authenticated user, **When** they create a task with reminder_at but no due_date, **Then** the system rejects with 422: "Reminder requires a due date."
5. **Given** an authenticated user, **When** they create a task with reminder_at after due_date, **Then** the system rejects with 422: "Reminder must be before due date."

---

### User Story 2 — Recurring Task Lifecycle (Priority: P1)

An authenticated user creates a recurring task that automatically generates new instances on schedule.

**Why this priority**: Recurring tasks are a key differentiator that makes the app genuinely useful for habits and repeated responsibilities.

**Independent Test**: Create a weekly recurring task, mark it complete, verify a new instance is auto-generated for the next week.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they create a task with recurrence_pattern "weekly", recurrence_interval 1, and due_date "2026-02-28", **Then** the task is created with recurrence fields stored. No Dapr Job is scheduled (recurrence is completion-based).
2. **Given** a recurring task with due_date "2026-02-28", **When** the user completes it, **Then** a `task.completed` event is published, the Recurring Task Service consumes it, and a new task instance is created with `due_date` advanced by one interval (to "2026-03-07"), same recurrence fields, `source_task_id` pointing to the original, and `status` reset to "pending".
3. **Given** a recurring task with `recurrence_ends_at` set, **When** the user completes it and the next computed due_date would be after `recurrence_ends_at`, **Then** no new instance is generated.
4. **Given** a recurring task, **When** the user deletes the original (source) task, **Then** no further instances can be generated. Existing generated instances remain.
5. **Given** a recurring task with `recurrence_pattern: "weekly"` and `recurrence_interval: 2`, **When** the user completes it, **Then** the next instance's due_date is advanced by 2 weeks.

---

### User Story 3 — Tag Management (Priority: P1)

An authenticated user creates tags and associates them with tasks for categorization.

**Why this priority**: Tags enable the filter/search experience that underpins all intermediate features.

**Independent Test**: Create two tags ("Work", "Personal"), create a task, assign both tags, verify tags appear on the task. Filter tasks by tag.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they create a tag with name "Work" and color "#3498DB", **Then** the tag is created with an auto-generated slug "work" and associated with their user_id.
2. **Given** a user with tags "Work" and "Personal", **When** they create a task with `tag_ids: [work-uuid, personal-uuid]`, **Then** the task is associated with both tags and they appear in the task response.
3. **Given** a user with a tag "Work" used on 5 tasks, **When** they delete the tag, **Then** the tag is removed and all 5 task-tag associations are deleted. The tasks themselves remain.
4. **Given** a user, **When** they create a tag with a name that already exists (case-insensitive), **Then** the system rejects with 409: "Tag already exists."
5. **Given** User A with a tag "Work", **When** User B creates a tag "Work", **Then** both tags are created independently — tags are scoped per user.

---

### User Story 4 — Search Tasks (Priority: P1)

An authenticated user searches across their tasks using a text query.

**Why this priority**: Search is essential for users with many tasks to quickly find what they need.

**Independent Test**: Create 5 tasks with varied titles, search for a keyword, verify only matching tasks are returned.

**Acceptance Scenarios**:

1. **Given** a user with tasks "Buy groceries", "Buy birthday gift", "Call dentist", **When** they search for "buy", **Then** both "Buy groceries" and "Buy birthday gift" are returned.
2. **Given** a user with a task with description "Pick up milk from the store", **When** they search for "milk", **Then** the task is returned (search includes description).
3. **Given** a user, **When** they search for "xyznonexistent", **Then** an empty result set is returned.
4. **Given** a user, **When** they search for "groceries" combined with filter `priority=high`, **Then** only matching tasks with high priority are returned.

---

### User Story 5 — Filter and Sort Tasks (Priority: P2)

An authenticated user filters their tasks by multiple criteria and sorts results.

**Why this priority**: Filtering and sorting make the task list manageable as the number of tasks grows. Depends on tags (Story 3) for tag filtering.

**Independent Test**: Create tasks with varied statuses, priorities, due dates, and tags. Apply filter combinations and verify correct results. Apply sort and verify ordering.

**Acceptance Scenarios**:

1. **Given** a user with tasks at various priorities, **When** they filter by `priority=critical`, **Then** only critical-priority tasks are returned.
2. **Given** a user with tasks due this week and next month, **When** they filter by `due_before=2026-03-01`, **Then** only tasks due before March 1 are returned.
3. **Given** a user with overdue tasks, **When** they filter by `overdue=true`, **Then** only tasks with past due dates and non-completed status are returned.
4. **Given** a user with tagged tasks, **When** they filter by `tag=work`, **Then** only tasks tagged "work" are returned.
5. **Given** a user, **When** they sort by `sort_by=priority&sort_order=desc`, **Then** tasks are returned in order: critical → high → medium → low.
6. **Given** a user, **When** they sort by `sort_by=due_date&sort_order=asc`, **Then** tasks are returned with earliest due dates first. Tasks with no due date appear last.
7. **Given** a user, **When** they combine `status=pending&tag=work&sort_by=due_date&sort_order=asc`, **Then** only pending work-tagged tasks are returned, sorted by due date ascending.

---

### User Story 6 — Event-Driven Task Lifecycle (Priority: P2)

When a user performs task operations, domain events flow through Kafka and trigger downstream processing.

**Why this priority**: The event backbone is the architectural foundation of Phase V. All advanced features depend on it.

**Independent Test**: Create a task, verify `task.created` event appears in Kafka topic. Update the task, verify `task.updated` event. Complete it, verify `task.completed` event. Delete it, verify `task.deleted` event.

**Acceptance Scenarios**:

1. **Given** a task creation request, **When** the task is persisted to PostgreSQL, **Then** a `task.created` event is published to `todo.task.created` Kafka topic within 500ms.
2. **Given** a `task.created` event with recurrence fields, **When** the Recurring Task Service consumes it, **Then** a Dapr Job is scheduled with the specified cron pattern.
3. **Given** a `task.completed` event for a recurring task, **When** the Recurring Task Service consumes it, **Then** a new task instance is created via service invocation to the Task API.
4. **Given** a `task.deleted` event, **When** the Reminder Service consumes it, **Then** any pending Dapr Jobs for that task are cancelled.
5. **Given** Kafka is temporarily unavailable, **When** a task is created, **Then** the task is still persisted to PostgreSQL (eventual consistency — event publishing retries with exponential backoff).

---

### User Story 7 — Local Deployment via Minikube (Priority: P2)

A developer deploys the entire system locally using Minikube with all services, Dapr sidecars, and observability.

**Why this priority**: Local deployment is the foundation for all testing and iteration before production.

**Independent Test**: Run `minikube start`, apply Kubernetes manifests, verify all pods are running, access the application via Minikube ingress, create a task, verify event flow.

**Acceptance Scenarios**:

1. **Given** a fresh Minikube cluster, **When** the developer applies all manifests with `kubectl apply -k ./k8s/local/`, **Then** all pods (frontend, task-api, reminder-service, recurring-task-service, redis) reach Ready state within 3 minutes.
2. **Given** all pods running, **When** the developer accesses the frontend via Minikube ingress, **Then** the application loads and is fully functional.
3. **Given** Dapr is installed in the cluster, **When** pods start, **Then** Dapr sidecars are injected and healthy (verified via `dapr status -k`).
4. **Given** a local Redpanda instance or Kafka stub, **When** a task is created, **Then** events flow through the local Kafka and consumers process them.

---

### User Story 8 — Production Kubernetes Deployment (Priority: P3)

The system is deployed to a production-grade managed Kubernetes cluster with TLS, autoscaling, and managed Kafka.

**Why this priority**: Production deployment is the final deliverable but depends on all other features being stable.

**Independent Test**: Deploy to AKS, verify TLS termination at ingress, create a task, verify end-to-end flow including Redpanda Cloud events.

**Acceptance Scenarios**:

1. **Given** a managed Kubernetes cluster, **When** the CI/CD pipeline runs on merge to main, **Then** container images are built, pushed to registry, and deployed to the cluster automatically.
2. **Given** production deployment, **When** the application is accessed via the public domain, **Then** TLS is enforced (HTTPS only) and the application is fully functional.
3. **Given** production deployment, **When** traffic increases, **Then** Horizontal Pod Autoscaler scales Task API pods from 2 to a maximum of 5 based on CPU/memory thresholds.
4. **Given** production deployment with Redpanda Cloud, **When** a task event is published, **Then** the event is delivered to Redpanda Cloud with SASL authentication and consumers process it.

---

### User Story 9 — CI/CD Pipeline (Priority: P3)

GitHub Actions builds, tests, and deploys the application automatically on code changes.

**Why this priority**: CI/CD accelerates iteration and ensures quality gates are enforced.

**Independent Test**: Push a commit, verify the pipeline runs lint + test + build + deploy stages.

**Acceptance Scenarios**:

1. **Given** a pull request is opened, **When** GitHub Actions triggers, **Then** lint, type-check, and unit tests run for both frontend and backend. The PR is blocked if any check fails.
2. **Given** a merge to the `main` branch, **When** GitHub Actions triggers, **Then** Docker images are built (multi-stage), tagged with commit SHA, and pushed to the container registry.
3. **Given** images are pushed, **When** the deploy stage runs, **Then** Kubernetes manifests are updated with the new image tag and applied to the production cluster.
4. **Given** a deployment failure, **When** the health check fails after rollout, **Then** Kubernetes automatically rolls back to the previous version.

---

### User Story 10 — Monitoring, Logging, and Tracing (Priority: P3)

The system provides observability through metrics, logs, and distributed traces.

**Why this priority**: Observability is critical for production reliability but depends on the application being deployed first.

**Independent Test**: Create a task, verify the request appears in Grafana dashboards, structured logs, and distributed trace.

**Acceptance Scenarios**:

1. **Given** Prometheus is deployed, **When** the Task API serves requests, **Then** HTTP request metrics (count, latency, status code) are collected and visible in Grafana.
2. **Given** structured logging is configured, **When** a request is processed, **Then** logs are emitted in JSON format with fields: timestamp, level, message, correlation_id, service, user_id.
3. **Given** OpenTelemetry is configured, **When** a task creation triggers event processing across services, **Then** a single distributed trace links the API request → Kafka publish → consumer processing.
4. **Given** a service health check fails, **When** Kubernetes detects the failure, **Then** the pod is restarted and an alert is raised (via Grafana alerting or equivalent).

---

### Edge Cases

- What happens when Kafka is down during task creation? → Task is persisted to PostgreSQL; event publishing retries with exponential backoff (max 3 retries). If all retries fail, the event is written to a dead-letter table for manual replay.
- What happens when a recurring task's cron expression is invalid? → Rejected at API level with 422 validation error before any event is published.
- What happens when a user deletes all their tags? → Tasks remain; only tag associations are removed.
- What happens when a due date is set in the past? → Rejected at API level with 422: "Due date must be in the future."
- What happens when two services try to process the same event? → Kafka consumer group ensures each partition is consumed by exactly one instance. Idempotency keys (event_id) prevent duplicate processing.
- What happens when the Dapr sidecar is not ready? → Service waits for sidecar health check (Dapr startup probe). Requests fail with 503 until sidecar is ready.
- What happens when Redpanda Cloud auth credentials expire? → Health check `/api/ready` reports Kafka as disconnected. Alert fires. Credentials are rotated via Dapr Secrets Management without pod restart.
- What happens when a reminder fires but the task was already completed? → Reminder Service checks task status before acting. If completed, the reminder is logged and discarded (no user notification).
- What happens during a rolling deployment when old and new versions coexist? → Event schemas are backward compatible (additive changes only). Consumers handle unknown fields gracefully.

---

## 13. Requirements

### Functional Requirements

- **FR-027**: The system MUST support task due dates as optional ISO 8601 datetime fields.
- **FR-028**: The system MUST compute and expose `is_overdue` (true when `due_date < now()` AND `status != completed`).
- **FR-029**: The system MUST support scheduled reminders via Dapr Jobs API, triggered at the specified `reminder_at` time.
- **FR-030**: The system MUST support recurring tasks with patterns: daily, weekly, monthly, custom (cron).
- **FR-031**: The system MUST auto-generate the next recurring task instance when the current one is completed.
- **FR-032**: The system MUST support a `critical` priority level in addition to existing low/medium/high.
- **FR-033**: The system MUST support user-scoped tags with CRUD operations.
- **FR-034**: The system MUST support many-to-many task-tag associations.
- **FR-035**: The system MUST support full-text search across task title and description using PostgreSQL tsvector.
- **FR-036**: The system MUST support filtering tasks by: status, priority, tag, due date range, overdue.
- **FR-037**: The system MUST support sorting tasks by: created_at, due_date, priority, title.
- **FR-038**: The system MUST support pagination on task listing endpoints (page, page_size).
- **FR-039**: The system MUST publish domain events to Kafka for all task state changes (created, updated, completed, deleted).
- **FR-040**: The system MUST use Dapr Pub/Sub for all event publishing and subscribing.
- **FR-041**: The system MUST use Dapr Secrets Management for all secrets (no hardcoded or env-file secrets in production).
- **FR-042**: The system MUST use Dapr Service Invocation for inter-service communication in Kubernetes.
- **FR-043**: All domain events MUST follow the common envelope schema with event_id, event_type, timestamp, correlation_id, user_id, and data.
- **FR-044**: The system MUST maintain an audit log table populated from Kafka events.
- **FR-045**: The system MUST provide readiness probes that check database, Kafka, and Dapr connectivity.
- **FR-046**: Existing Phase II and III functionality (dashboard, chatbot) MUST remain fully functional.
- **FR-047**: The Phase III AI Chatbot's MCP tools MUST be extended to support new fields: due_date, reminder_at, tags, recurrence_pattern, recurrence_interval. Chatbot MUST support search and filter parameters in list_tasks.
- **FR-048**: Tags MUST be limited to max 50 per user and max 10 per task.
- **FR-049**: The system MUST support tag updates (rename and recolor) via `PATCH /api/tags/{tag_id}`.
- **FR-050**: Frontend MUST use SSR Proxy pattern — all API calls go through Next.js Route Handlers via Dapr sidecar to Task API. Browser never calls FastAPI directly.
- **FR-051**: Minikube deployment MUST use a local PostgreSQL container (not Neon). Neon is used only in production.

### Key Entities

- **Task** (extended): Todo item with due date, recurrence, reminder, tags, search vector, overdue flag.
- **Tag**: User-defined label with name, slug, color. Scoped per user.
- **TaskTag**: Junction table for many-to-many task-tag relationship.
- **AuditLog**: Immutable record of domain events for compliance and debugging.

---

## 14. Non-Functional Requirements

### Scalability

- **NFR-012**: The Task API MUST support horizontal scaling to 5 replicas without shared state.
- **NFR-013**: Kafka topics MUST be partitioned (minimum 3) to support parallel consumer processing.
- **NFR-014**: Task listing with filters MUST return within 500ms for users with up to 10,000 tasks.

### Decoupling

- **NFR-015**: Services MUST communicate only via Dapr (Pub/Sub or Service Invocation) — no direct HTTP between services in Kubernetes.
- **NFR-016**: Adding a new event consumer MUST NOT require changes to the event producer.
- **NFR-017**: Each service MUST be independently deployable and restartable without affecting others.

### Fault Tolerance

- **NFR-018**: Task creation MUST succeed even if Kafka is temporarily unavailable (database-first, event-retry pattern).
- **NFR-019**: Kafka consumers MUST be idempotent — processing the same event twice MUST produce the same result.
- **NFR-020**: Failed event processing MUST be retried 3 times with exponential backoff before moving to a dead-letter topic.
- **NFR-021**: Service restarts MUST resume Kafka consumption from the last committed offset (no message loss).

### Security

- **NFR-022**: All secrets MUST be managed via Dapr Secrets Management backed by Kubernetes Secrets (local) or cloud vault (production).
- **NFR-023**: Kafka connections MUST use SASL/SCRAM authentication in production.
- **NFR-024**: Kubernetes network policies MUST restrict inter-pod communication to only necessary paths.
- **NFR-025**: Container images MUST use non-root users and minimal base images.

### Observability

- **NFR-026**: All services MUST emit structured JSON logs with correlation_id, service name, and log level.
- **NFR-027**: HTTP request metrics (latency, count, error rate) MUST be exposed via Prometheus-compatible endpoints.
- **NFR-028**: Distributed traces MUST span across service boundaries (API → Kafka → consumer) via OpenTelemetry.
- **NFR-029**: Grafana dashboards MUST display: request rate, error rate, p95 latency, Kafka consumer lag, pod resource usage.

### Performance

- **NFR-030**: API response times MUST be under 500ms at p95 for read operations and under 1 second for write operations (including event publishing).
- **NFR-031**: Event publishing to Kafka MUST complete within 200ms at p95.
- **NFR-032**: Full-text search queries MUST complete within 300ms for datasets up to 100,000 tasks (across all users).

---

## 15. Success Criteria

### Measurable Outcomes

- **SC-015**: A user can create a task with due date, reminder, tags, and recurrence in under 5 seconds (API response time).
- **SC-016**: A `task.created` event appears in Kafka within 500ms of API response.
- **SC-017**: A recurring task generates its next instance within 5 seconds of the previous instance being completed.
- **SC-018**: A scheduled reminder fires within 60 seconds of its `reminder_at` time.
- **SC-019**: Full-text search returns results within 300ms for a user with 1,000 tasks.
- **SC-020**: The entire system deploys to Minikube from scratch in under 5 minutes.
- **SC-021**: The CI/CD pipeline completes (build → test → deploy) in under 10 minutes.
- **SC-022**: All services show healthy status in Grafana with zero unhandled errors in a 24-hour production window.
- **SC-023**: Existing dashboard and chatbot features have zero regressions from Phase IV.
- **SC-024**: System sustains 100 concurrent users with p95 latency under 1 second.

---

## 16. Assumptions

- Redpanda Cloud free tier or trial is available for managed Kafka.
- The managed Kubernetes cluster (AKS/GKE/OKE) free tier or credits are available.
- Dapr runtime version 1.14+ is used (supports Jobs API).
- Neon PostgreSQL supports tsvector full-text search on the current plan.
- GitHub Container Registry (ghcr.io) is used for container image storage.
- The existing codebase from Phase IV is the starting point.
- Helm 3 is used for Kubernetes package management.
- Users interact in English (no i18n for search).
- Reminder "delivery" is log-only in this phase (no email/SMS/push).

---

## 17. Deployment Architecture

### 17.1 Local (Minikube)

```
minikube/
├── namespace.yaml
├── dapr/
│   ├── pubsub-kafka.yaml         # Local Redpanda or Kafka container
│   ├── statestore-redis.yaml
│   ├── secrets-kubernetes.yaml
│   └── subscription.yaml
├── services/
│   ├── task-api.yaml             # Deployment + Service + Dapr annotations
│   ├── reminder-service.yaml
│   ├── recurring-task-service.yaml
│   └── frontend.yaml
├── infrastructure/
│   ├── redis.yaml
│   ├── redpanda.yaml             # Local Redpanda (Kafka-compatible)
│   └── postgres.yaml             # Optional local PG (or use Neon)
├── monitoring/
│   ├── prometheus.yaml
│   ├── grafana.yaml
│   └── otel-collector.yaml
├── ingress.yaml
└── kustomization.yaml
```

### 17.2 Production (AKS — Azure)

```
k8s/production/
├── namespace.yaml
├── dapr/
│   ├── pubsub-kafka.yaml         # Points to Redpanda Cloud
│   ├── statestore-redis.yaml     # Azure Cache for Redis or in-cluster
│   ├── secrets-keyvault.yaml     # Azure Key Vault
│   └── subscription.yaml
├── services/
│   ├── task-api.yaml             # + HPA + PDB + resource limits
│   ├── reminder-service.yaml
│   ├── recurring-task-service.yaml
│   └── frontend.yaml
├── networking/
│   ├── ingress.yaml              # With TLS cert
│   └── network-policies.yaml
├── monitoring/
│   ├── prometheus.yaml
│   ├── grafana.yaml
│   └── otel-collector.yaml
├── hpa.yaml
└── kustomization.yaml
```

### 17.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci-cd.yaml
name: CI/CD Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-and-test:
    # Runs on PR: lint, type-check, unit tests

  build-and-push:
    # Runs on main merge: build Docker images, push to ghcr.io

  deploy-staging:
    # Runs after build: deploy to staging namespace

  deploy-production:
    # Manual approval gate: deploy to production namespace
```

---

## 18. Glossary

| Term | Definition |
|------|-----------|
| **Domain Event** | An immutable record of a state change (e.g., task.created) published to Kafka |
| **Event Envelope** | Standard wrapper containing event metadata (id, type, timestamp, correlation_id) |
| **Dapr Sidecar** | A companion container injected alongside each service pod that handles Dapr building block calls |
| **Pub/Sub** | Publish/Subscribe messaging pattern via Kafka (Dapr abstraction) |
| **Dead-Letter Topic** | A Kafka topic for events that failed processing after all retries |
| **Consumer Group** | A set of Kafka consumers that share the load of consuming from topic partitions |
| **HPA** | Horizontal Pod Autoscaler — Kubernetes resource that scales pods based on metrics |
| **PDB** | Pod Disruption Budget — ensures minimum availability during voluntary disruptions |
| **tsvector** | PostgreSQL data type for full-text search indexing |
| **Correlation ID** | A UUID propagated across all services in a single request chain for tracing |
| **Idempotency** | The property that processing an event multiple times has the same effect as processing it once |
| **Redpanda** | Kafka-compatible streaming platform, used as managed Kafka (Redpanda Cloud) |

---

## 19. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Redpanda Cloud free tier limits exceeded | Events stop flowing | Medium | Monitor usage; fall back to in-cluster Redpanda |
| Dapr Jobs API instability (relatively new) | Reminders/recurrence fail | Medium | Implement fallback scheduler; pin Dapr version |
| Kubernetes cost overrun | Budget exceeded | Low | Use spot/preemptible nodes; set resource limits |
| Event schema evolution breaks consumers | Consumer crashes | Medium | Additive-only schema changes; schema versioning |
| Neon PostgreSQL full-text search performance | Slow search | Low | Add GIN indexes; consider dedicated search (future) |

---

## 20. Deliverables Checklist

### Advanced Features
- [ ] **D-015**: Due date field on tasks with validation and overdue detection
- [ ] **D-016**: Scheduled reminders via Dapr Jobs API
- [ ] **D-017**: Recurring task patterns (daily, weekly, monthly, custom cron)
- [ ] **D-018**: Auto-generation of next recurring task instance on completion

### Intermediate Features
- [ ] **D-019**: Critical priority level added
- [ ] **D-020**: Tag CRUD endpoints and task-tag associations
- [ ] **D-021**: Full-text search across title and description
- [ ] **D-022**: Multi-criteria filtering (status, priority, tag, due date, overdue)
- [ ] **D-023**: Multi-field sorting (created_at, due_date, priority, title)
- [ ] **D-024**: Paginated task listing

### Event-Driven Architecture
- [ ] **D-025**: Kafka topic definitions and provisioning
- [ ] **D-026**: Event envelope schema implementation
- [ ] **D-027**: Task API publishes domain events on all state changes
- [ ] **D-028**: Reminder Service consumes and processes reminder events
- [ ] **D-029**: Recurring Task Service consumes and processes recurring events
- [ ] **D-030**: Dead-letter handling for failed events
- [ ] **D-031**: Audit log populated from Kafka events

### Dapr Integration
- [ ] **D-032**: Dapr Pub/Sub component (Kafka-backed)
- [ ] **D-033**: Dapr State Management component (Redis-backed)
- [ ] **D-034**: Dapr Jobs API integration for reminders and recurrence
- [ ] **D-035**: Dapr Secrets Management for all secrets
- [ ] **D-036**: Dapr Service Invocation for inter-service calls

### Deployment
- [ ] **D-037**: Dockerfiles for all services (multi-stage builds)
- [ ] **D-038**: Kubernetes manifests for Minikube deployment
- [ ] **D-039**: Minikube deployment script with all dependencies
- [ ] **D-040**: Production Kubernetes manifests (AKS)
- [ ] **D-041**: Ingress with TLS configuration
- [ ] **D-042**: HPA configuration for Task API

### CI/CD
- [ ] **D-043**: GitHub Actions lint + test workflow (PR gate)
- [ ] **D-044**: GitHub Actions build + push workflow (main branch)
- [ ] **D-045**: GitHub Actions deploy workflow (staging + production)

### Monitoring & Logging
- [ ] **D-046**: Structured JSON logging across all services
- [ ] **D-047**: Prometheus metrics endpoints
- [ ] **D-048**: Grafana dashboards (request rate, latency, errors, Kafka lag)
- [ ] **D-049**: OpenTelemetry distributed tracing
- [ ] **D-050**: Health and readiness probes on all services

### Chatbot Updates
- [ ] **D-051**: MCP tools extended with due_date, reminder_at, tags, recurrence fields
- [ ] **D-052**: Chatbot list_tasks tool supports search and filter parameters
- [ ] **D-053**: Chatbot handles new features via natural language (e.g., "add task due Friday tagged work")

### Backward Compatibility
- [ ] **D-054**: Phase II dashboard fully functional
- [ ] **D-055**: Phase III chatbot fully functional (plus new features)
- [ ] **D-056**: Existing API endpoints backward compatible
