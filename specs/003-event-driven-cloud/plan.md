# Implementation Plan: Phase V — Advanced Event-Driven Cloud Deployment

**Branch**: `003-event-driven-cloud` | **Date**: 2026-02-22 | **Spec**: `specs/003-event-driven-cloud/spec.md`
**Input**: Feature specification from `specs/003-event-driven-cloud/spec.md`

---

## Summary

Evolve the Todo application from a monolithic request-response architecture into a microservice-based, event-driven, cloud-native system. The plan defines six microservices (Task API, Chat API, Reminder Service, Recurring Task Service, Audit Service, WebSocket Sync Service), a Kafka event backbone via Dapr Pub/Sub, Kubernetes deployment for both Minikube (local) and AKS (cloud), CI/CD via GitHub Actions, and a Prometheus + Grafana + OpenTelemetry observability stack.

---

## Technical Context

**Language/Version**: Python 3.12 (backend services), TypeScript 5.x / Node.js 22 (frontend)
**Primary Dependencies**: FastAPI, SQLModel, Dapr SDK (Python), Next.js 16+, Tailwind CSS
**Storage**: PostgreSQL (Neon Serverless — production, local container — Minikube), Redis (Dapr state store)
**Event Streaming**: Apache Kafka via Redpanda Cloud (production), Strimzi (local Minikube)
**Runtime Abstraction**: Dapr 1.14+ (Pub/Sub, State, Jobs, Secrets, Service Invocation)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Kubernetes — Minikube (local), AKS (production)
**Project Type**: Microservice monorepo
**Performance Goals**: p95 < 500ms reads, p95 < 1s writes, search < 300ms, event publish < 200ms
**Constraints**: SASL/SCRAM Kafka auth in production, non-root containers, no direct inter-service HTTP, JWT auth on all endpoints
**Scale/Scope**: 100 concurrent users, 100K tasks total, 5 replicas max HPA

---

## Constitution Check

*GATE: Verified against Constitution v2.0.0*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | PASS | Spec v1 (clarified) complete at `specs/003-event-driven-cloud/spec.md` |
| II. Security-First | PASS | JWT on all endpoints, SASL Kafka, Dapr Secrets, non-root containers, user isolation |
| III. Clean Code & Separation | PASS | Microservice boundaries; Dapr-only inter-service comms |
| IV. Stateless Auth | PASS | JWT HS256, no session stores |
| V. Production-Ready | PASS | Health/readiness probes, structured logging, error format |
| VI. Smallest Viable Diff | PASS | Plan scoped to spec deliverables D-015 through D-056 |
| VII. No Dead Code | PASS | No carry-over of unused Phase IV artifacts |
| VIII. Acceptance Criteria | PASS | All 10 user stories with Given/When/Then defined in spec |
| IX. Demo-Ready | PASS | Responsive UI, Grafana dashboards, presentable |
| X. Explicit Over Implicit | PASS | Dapr components, typed models, injected dependencies |
| XI. Event-Driven Architecture | PASS | Kafka via Dapr Pub/Sub, envelope schema, idempotent consumers |
| XII. Cloud-Native Deployment | PASS | Docker multi-stage, K8s manifests, HPA, CI/CD |
| XIII. Observability-First | PASS | Prometheus, Grafana, OpenTelemetry, structured JSON logs |

---

## 1. Service Architecture

### 1.1 Service Decomposition

The system comprises **six microservices** plus **infrastructure components**.

| # | Service | Language | Framework | Port | Dapr App ID | Responsibility |
|---|---------|----------|-----------|------|-------------|----------------|
| 1 | **Task API** | Python 3.12 | FastAPI | 8000 | `task-api` | Task CRUD, tags, search, filter, sort, pagination. Publishes domain events. Consumes `todo.audit.log` for audit persistence. |
| 2 | **Chat API** | Python 3.12 | FastAPI | 8001 | `chat-api` | AI chatbot endpoint. MCP tools extended for due dates, tags, reminders, search, filter. OpenAI Agents SDK integration. |
| 3 | **Reminder Service** | Python 3.12 | FastAPI | 8002 | `reminder-service` | Consumes `reminder.scheduled` / `task.deleted` / `task.updated` events. Schedules one-time Dapr Jobs. Publishes `reminder.triggered`. |
| 4 | **Recurring Task Service** | Python 3.12 | FastAPI | 8003 | `recurring-service` | Consumes `task.completed` events. Computes next due date. Creates next instance via Dapr Service Invocation → Task API. |
| 5 | **Audit Service** | Python 3.12 | FastAPI | 8004 | `audit-service` | Consumes all `todo.audit.log` events. Writes to AuditLog table. Provides audit query endpoints. |
| 6 | **WebSocket Sync Service** | Python 3.12 | FastAPI | 8005 | `ws-sync-service` | Consumes all `todo.task.*` events. Pushes real-time updates to connected clients via WebSocket. |
| 7 | **Frontend** | TypeScript | Next.js 16+ | 3000 | `frontend` | SSR proxy to Task API via Dapr sidecar. UI for tasks, tags, search, filter, sort, chatbot. |

> **Note on Audit Service**: The spec states "Task API self-consumes `todo.audit.log`." Per the user's architecture requirements, audit is extracted to a dedicated Audit Service. This is an upgrade from the spec — the Audit Service takes over the audit-log subscription, removing that responsibility from Task API.

> **Note on WebSocket Sync Service**: This is a new service not in the original spec (spec Section 5 explicitly lists WebSocket/SSE as out-of-scope). Per the user's architecture requirements, this service is added to provide real-time task updates to connected frontend clients.

### 1.2 Service Responsibility Matrix

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE RESPONSIBILITY MATRIX                        │
├─────────────────────┬────────┬────────┬──────────┬──────────┬───────┬────────┤
│ Capability          │Task API│Chat API│Reminder  │Recurring │Audit  │WS Sync │
├─────────────────────┼────────┼────────┼──────────┼──────────┼───────┼────────┤
│ Task CRUD           │   ●    │        │          │          │       │        │
│ Tag CRUD            │   ●    │        │          │          │       │        │
│ Search/Filter/Sort  │   ●    │        │          │          │       │        │
│ Pagination          │   ●    │        │          │          │       │        │
│ Event Publishing    │   ●    │        │    ●     │          │       │        │
│ JWT Auth            │   ●    │   ●    │          │          │  ●    │   ●    │
│ MCP Tools           │        │   ●    │          │          │       │        │
│ Chatbot NLP         │        │   ●    │          │          │       │        │
│ Job Scheduling      │        │        │    ●     │          │       │        │
│ Reminder Trigger    │        │        │    ●     │          │       │        │
│ Recurrence Compute  │        │        │          │    ●     │       │        │
│ Audit Persistence   │        │        │          │          │   ●   │        │
│ Audit Queries       │        │        │          │          │   ●   │        │
│ Real-time Push      │        │        │          │          │       │   ●    │
│ WebSocket Mgmt      │        │        │          │          │       │   ●    │
│ Health Probes       │   ●    │   ●    │    ●     │    ●     │   ●   │   ●    │
│ Metrics Export      │   ●    │   ●    │    ●     │    ●     │   ●   │   ●    │
└─────────────────────┴────────┴────────┴──────────┴──────────┴───────┴────────┘
```

---

## 2. API Contracts

### 2.1 Task API (`task-api` — port 8000)

All endpoints require `Authorization: Bearer <jwt>` except health/readiness.

#### Task Endpoints

| Method | Path | Description | Events Emitted |
|--------|------|-------------|----------------|
| `GET` | `/api/tasks` | List tasks with search, filter, sort, pagination | — |
| `POST` | `/api/tasks` | Create task (with optional due_date, tags, recurrence, reminder) | `task.created`, `reminder.scheduled` (if reminder_at set) |
| `GET` | `/api/tasks/{task_id}` | Get single task | — |
| `PUT` | `/api/tasks/{task_id}` | Full update task | `task.updated`, `reminder.scheduled` (if reminder_at changed) |
| `PATCH` | `/api/tasks/{task_id}` | Partial update task | `task.updated`, `reminder.scheduled` (if reminder_at changed) |
| `DELETE` | `/api/tasks/{task_id}` | Delete task | `task.deleted` |
| `PATCH` | `/api/tasks/{task_id}/complete` | Mark task completed | `task.completed` |
| `GET` | `/api/tasks/overdue` | List overdue tasks | — |
| `POST` | `/api/tasks/{task_id}/tags` | Add tags to task | `task.updated` |
| `DELETE` | `/api/tasks/{task_id}/tags/{tag_id}` | Remove tag from task | `task.updated` |

#### Tag Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tags` | List user's tags (with task_count) |
| `POST` | `/api/tags` | Create tag |
| `PATCH` | `/api/tags/{tag_id}` | Update tag (name, color) |
| `DELETE` | `/api/tags/{tag_id}` | Delete tag and associations |

#### Auth Endpoints (Phase II — unchanged)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/signup` | Register new user |
| `POST` | `/api/auth/token` | Login, get JWT |
| `GET` | `/api/auth/me` | Get current user |

#### Probe Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness probe — `{"status": "healthy"}` |
| `GET` | `/api/ready` | Readiness probe — checks DB, Kafka, Dapr |

#### Query Parameters for `GET /api/tasks`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | `string` | — | Filter: pending, in_progress, completed |
| `priority` | `string` | — | Filter: low, medium, high, critical |
| `tag` | `string` (repeatable) | — | Filter by tag slug |
| `due_before` | `datetime` | — | Filter: due date before |
| `due_after` | `datetime` | — | Filter: due date after |
| `overdue` | `boolean` | — | Filter: only overdue tasks |
| `search` | `string` | — | Full-text search (tsvector) |
| `sort_by` | `string` | `created_at` | Sort field: created_at, due_date, priority, title |
| `sort_order` | `string` | `desc` | Sort direction: asc, desc |
| `page` | `integer` | `1` | Page number |
| `page_size` | `integer` | `20` | Items per page (max 100) |

### 2.2 Chat API (`chat-api` — port 8001)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send message, get AI response |
| `GET` | `/api/conversations` | List user conversations |
| `GET` | `/api/conversations/{id}` | Get conversation with messages |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/ready` | Readiness probe |

**Extended MCP Tools** (invoked by AI agent):

| Tool | Extension |
|------|-----------|
| `add_task` | New params: `due_date`, `reminder_at`, `recurrence_pattern`, `recurrence_interval`, `tag_ids` |
| `list_tasks` | New params: `search`, `status`, `priority`, `tag`, `due_before`, `due_after`, `overdue`, `sort_by`, `sort_order` |
| `update_task` | New params: `due_date`, `reminder_at`, `tag_ids` |
| `add_tag` | New tool: create user tag |
| `list_tags` | New tool: list user tags |
| `search_tasks` | New tool: full-text search shortcut |

### 2.3 Reminder Service (`reminder-service` — port 8002)

No external API — event-driven only.

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Liveness probe |
| `GET /api/ready` | Readiness probe |
| `POST /dapr/subscribe` | Dapr subscription registration |
| `POST /events/reminder-scheduled` | Dapr Pub/Sub handler for `todo.reminder.scheduled` |
| `POST /events/task-deleted` | Dapr Pub/Sub handler for `todo.task.deleted` |
| `POST /events/task-updated` | Dapr Pub/Sub handler for `todo.task.updated` |
| `POST /jobs/reminder-triggered` | Dapr Jobs callback when a scheduled reminder fires |

### 2.4 Recurring Task Service (`recurring-service` — port 8003)

No external API — event-driven only.

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Liveness probe |
| `GET /api/ready` | Readiness probe |
| `POST /dapr/subscribe` | Dapr subscription registration |
| `POST /events/task-completed` | Dapr Pub/Sub handler for `todo.task.completed` |

**Internal Flow**: On `task.completed` with recurrence fields → compute next due date → call Task API via Dapr Service Invocation (`POST /api/tasks`) with `source_task_id` set to original task.

### 2.5 Audit Service (`audit-service` — port 8004)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Liveness probe |
| `GET /api/ready` | Readiness probe |
| `POST /dapr/subscribe` | Dapr subscription registration |
| `POST /events/audit-log` | Dapr Pub/Sub handler for `todo.audit.log` |
| `GET /api/audit` | Query audit logs (JWT required, scoped to user) |
| `GET /api/audit/{task_id}` | Audit trail for a specific task |

### 2.6 WebSocket Sync Service (`ws-sync-service` — port 8005)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Liveness probe |
| `GET /api/ready` | Readiness probe |
| `WS /ws/tasks` | WebSocket endpoint — clients connect with JWT in query param |
| `POST /dapr/subscribe` | Dapr subscription registration |
| `POST /events/task-created` | Push task creation to connected clients |
| `POST /events/task-updated` | Push task update to connected clients |
| `POST /events/task-completed` | Push task completion to connected clients |
| `POST /events/task-deleted` | Push task deletion to connected clients |
| `POST /events/reminder-triggered` | Push reminder notification to connected clients |

**WebSocket Message Format**:
```json
{
  "type": "task.created",
  "data": { "task_id": "uuid", "title": "...", ... },
  "timestamp": "2026-02-22T10:30:00Z"
}
```

---

## 3. Event Publishing / Subscription Matrix

### 3.1 Kafka Topics

| Topic | Partitions | Retention | Key | Schema Version |
|-------|-----------|-----------|-----|----------------|
| `todo.task.created` | 3 | 7 days | `user_id` | v1.0 |
| `todo.task.updated` | 3 | 7 days | `user_id` | v1.0 |
| `todo.task.completed` | 3 | 7 days | `user_id` | v1.0 |
| `todo.task.deleted` | 3 | 7 days | `user_id` | v1.0 |
| `todo.reminder.scheduled` | 3 | 7 days | `task_id` | v1.0 |
| `todo.reminder.triggered` | 3 | 3 days | `task_id` | v1.0 |
| `todo.audit.log` | 6 | 30 days | `user_id` | v1.0 |
| `todo.task.dlq` | 1 | 90 days | `event_id` | v1.0 |

### 3.2 Publisher Matrix

| Producer | Topics Published |
|----------|-----------------|
| **Task API** | `todo.task.created`, `todo.task.updated`, `todo.task.completed`, `todo.task.deleted`, `todo.reminder.scheduled`, `todo.audit.log` |
| **Reminder Service** | `todo.reminder.triggered` |

### 3.3 Subscriber Matrix

| Consumer | Topics Subscribed | Consumer Group | Action |
|----------|------------------|----------------|--------|
| **Reminder Service** | `todo.reminder.scheduled` | `reminder-svc` | Schedule Dapr Job at `reminder_at` time |
| **Reminder Service** | `todo.task.deleted` | `reminder-svc` | Cancel pending Dapr Job for deleted task |
| **Reminder Service** | `todo.task.updated` | `reminder-svc` | Reschedule Dapr Job if `reminder_at` changed |
| **Recurring Task Service** | `todo.task.completed` | `recurring-svc` | Generate next instance if task has recurrence |
| **Audit Service** | `todo.audit.log` | `audit-svc` | Persist event to AuditLog table |
| **WS Sync Service** | `todo.task.created` | `ws-sync-svc` | Push to connected WebSocket clients |
| **WS Sync Service** | `todo.task.updated` | `ws-sync-svc` | Push to connected WebSocket clients |
| **WS Sync Service** | `todo.task.completed` | `ws-sync-svc` | Push to connected WebSocket clients |
| **WS Sync Service** | `todo.task.deleted` | `ws-sync-svc` | Push to connected WebSocket clients |
| **WS Sync Service** | `todo.reminder.triggered` | `ws-sync-svc` | Push reminder notification to clients |

### 3.4 Event Flow Diagrams

#### Flow 1: Task Creation with Reminder

```
User → Frontend → Dapr Sidecar → Task API
                                    │
                                    ├── 1. Persist to PostgreSQL
                                    ├── 2. Publish → todo.task.created
                                    ├── 3. Publish → todo.reminder.scheduled (if reminder_at set)
                                    └── 4. Publish → todo.audit.log
                                              │
                    ┌─────────────────────────┼──────────────────────────┐
                    ▼                         ▼                          ▼
            Reminder Service          Audit Service            WS Sync Service
            (schedule Dapr Job)       (persist audit log)      (push to clients)
```

#### Flow 2: Task Completion with Recurrence

```
User → Frontend → Dapr Sidecar → Task API
                                    │
                                    ├── 1. Update status → completed
                                    ├── 2. Publish → todo.task.completed
                                    └── 3. Publish → todo.audit.log
                                              │
                    ┌─────────────────────────┼──────────────────────────┐
                    ▼                         ▼                          ▼
          Recurring Task Service       Audit Service            WS Sync Service
                    │                 (persist audit log)      (push to clients)
                    │
                    ▼
          Compute next due_date
                    │
                    ▼
          Dapr Service Invocation → Task API (POST /api/tasks)
                                    │
                                    ├── Persist new instance
                                    ├── Publish → todo.task.created
                                    └── Publish → todo.audit.log
```

#### Flow 3: Reminder Firing

```
            Dapr Jobs API
                │
                ▼ (at reminder_at time)
        Reminder Service
                │
                ├── 1. Check task status (via Dapr Service Invocation → Task API)
                ├── 2. If task not completed → Publish → todo.reminder.triggered
                └── 3. Task API marks reminder_sent = true
                                │
                                ▼
                        WS Sync Service
                        (push notification to client)
```

---

## 4. Dapr Components

### 4.1 Component: `pubsub-kafka`

**Type**: `pubsub.kafka`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub-kafka
  namespace: todo-app
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    # --- Local (Strimzi in Minikube) ---
    # - name: brokers
    #   value: "strimzi-kafka-bootstrap.kafka:9092"
    # - name: authType
    #   value: "none"

    # --- Production (Redpanda Cloud) ---
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
    - name: consumeRetryInterval
      value: "1000ms"
    - name: version
      value: "3.0.0"
  auth:
    secretStore: secrets-store
```

### 4.2 Component: `statestore-postgresql`

**Type**: `state.postgresql`

> Per user requirements, using PostgreSQL state store (not Redis) for state management.

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
  namespace: todo-app
spec:
  type: state.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: db-secrets
        key: state-store-url
    - name: tableName
      value: "dapr_state"
    - name: metadataTableName
      value: "dapr_metadata"
    - name: actorStateStore
      value: "false"
  auth:
    secretStore: secrets-store
```

### 4.3 Component: `secrets-store`

**Type**: `secretstores.kubernetes` (local) / `secretstores.azure.keyvault` (production)

#### Local (Minikube)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: secrets-store
  namespace: todo-app
spec:
  type: secretstores.kubernetes
  version: v1
  metadata: []
```

#### Production (AKS + Azure Key Vault)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: secrets-store
  namespace: todo-app
spec:
  type: secretstores.azure.keyvault
  version: v1
  metadata:
    - name: vaultName
      value: "todo-app-keyvault"
    - name: azureClientId
      value: "<managed-identity-client-id>"
    - name: azureTenantId
      value: "<azure-tenant-id>"
```

### 4.4 Dapr Subscriptions

```yaml
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: reminder-subscriptions
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.reminder.scheduled
  routes:
    default: /events/reminder-scheduled
  scopes:
    - reminder-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: reminder-task-deleted
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.deleted
  routes:
    default: /events/task-deleted
  scopes:
    - reminder-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: reminder-task-updated
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.updated
  routes:
    default: /events/task-updated
  scopes:
    - reminder-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: recurring-task-completed
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.completed
  routes:
    default: /events/task-completed
  scopes:
    - recurring-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: audit-log-subscription
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.audit.log
  routes:
    default: /events/audit-log
  scopes:
    - audit-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: ws-sync-task-created
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.created
  routes:
    default: /events/task-created
  scopes:
    - ws-sync-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: ws-sync-task-updated
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.updated
  routes:
    default: /events/task-updated
  scopes:
    - ws-sync-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: ws-sync-task-completed
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.completed
  routes:
    default: /events/task-completed
  scopes:
    - ws-sync-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: ws-sync-task-deleted
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.task.deleted
  routes:
    default: /events/task-deleted
  scopes:
    - ws-sync-service
---
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: ws-sync-reminder-triggered
  namespace: todo-app
spec:
  pubsubname: pubsub-kafka
  topic: todo.reminder.triggered
  routes:
    default: /events/reminder-triggered
  scopes:
    - ws-sync-service
```

### 4.5 Dapr Jobs API Usage

The Jobs API is used **only by the Reminder Service** for scheduling one-time reminder notifications.

**Scheduling a Job** (Reminder Service → Dapr Sidecar):
```
POST http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}
Content-Type: application/json

{
  "dueTime": "2026-02-25T08:00:00Z",
  "data": {
    "@type": "type.googleapis.com/google.protobuf.Any",
    "value": {
      "task_id": "uuid",
      "user_id": "uuid",
      "task_title": "Buy groceries",
      "action": "trigger_reminder"
    }
  }
}
```

**Cancelling a Job** (when task is deleted or reminder_at changes):
```
DELETE http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}
```

**Job Callback** (Dapr → Reminder Service):
```
POST http://reminder-service:8002/jobs/reminder-triggered
Content-Type: application/json

{
  "task_id": "uuid",
  "user_id": "uuid",
  "task_title": "Buy groceries",
  "action": "trigger_reminder"
}
```

### 4.6 Dapr Service Invocation Patterns

| Caller | Target | Method | Route | Purpose |
|--------|--------|--------|-------|---------|
| Frontend (Next.js SSR) | Task API | `GET` | `/api/tasks` | List tasks |
| Frontend (Next.js SSR) | Task API | `POST` | `/api/tasks` | Create task |
| Frontend (Next.js SSR) | Task API | `*` | `/api/*` | All task/tag operations |
| Frontend (Next.js SSR) | Chat API | `POST` | `/api/chat` | Send chat message |
| Recurring Task Service | Task API | `POST` | `/api/tasks` | Create next recurring instance |
| Reminder Service | Task API | `PATCH` | `/api/tasks/{id}` | Set `reminder_sent = true` |
| Chat API | Task API | `*` | `/api/*` | MCP tool invocations |

**Invocation URL Pattern**:
```
http://localhost:{DAPR_HTTP_PORT}/v1.0/invoke/{app-id}/method/{route}
```

---

## 5. Deployment Topology

### 5.1 Minikube (Local Development)

#### Cluster Configuration

```
Minikube Cluster
├── Namespace: todo-app
│   ├── task-api (1 replica + Dapr sidecar)
│   ├── chat-api (1 replica + Dapr sidecar)
│   ├── reminder-service (1 replica + Dapr sidecar)
│   ├── recurring-service (1 replica + Dapr sidecar)
│   ├── audit-service (1 replica + Dapr sidecar)
│   ├── ws-sync-service (1 replica + Dapr sidecar)
│   ├── frontend (1 replica + Dapr sidecar)
│   ├── postgresql (1 replica, PVC)
│   └── Dapr Components (pubsub-kafka, statestore, secrets-kubernetes)
│
├── Namespace: kafka
│   └── Strimzi Kafka Operator
│       ├── Kafka Broker (1 replica)
│       └── Zookeeper (1 replica)  [or KRaft mode]
│
├── Namespace: monitoring
│   ├── Prometheus (1 replica)
│   ├── Grafana (1 replica)
│   └── OpenTelemetry Collector (1 replica)
│
├── Namespace: dapr-system
│   ├── dapr-operator
│   ├── dapr-sentry
│   ├── dapr-sidecar-injector
│   └── dapr-placement
│
└── Ingress: NGINX Ingress Controller
    ├── / → frontend:3000
    └── /api/* → (routed via frontend SSR proxy)
```

#### Local Kubernetes Manifests Structure

```
k8s/local/
├── namespaces/
│   ├── todo-app.yaml
│   ├── kafka.yaml
│   └── monitoring.yaml
├── infrastructure/
│   ├── postgresql/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── configmap.yaml       # init.sql
│   └── strimzi/
│       ├── kafka-cluster.yaml   # Strimzi KafkaCluster CR
│       └── kafka-topics.yaml    # KafkaTopic CRs for all topics
├── dapr/
│   ├── pubsub-kafka.yaml        # brokers: strimzi, authType: none
│   ├── statestore-postgresql.yaml
│   ├── secrets-kubernetes.yaml
│   └── subscriptions.yaml       # All Dapr subscriptions
├── secrets/
│   ├── db-secrets.yaml          # base64-encoded local DB creds
│   ├── jwt-secrets.yaml         # base64-encoded local JWT secret
│   └── openai-secrets.yaml      # base64-encoded OpenAI key
├── services/
│   ├── task-api.yaml            # Deployment + Service + Dapr annotations
│   ├── chat-api.yaml
│   ├── reminder-service.yaml
│   ├── recurring-service.yaml
│   ├── audit-service.yaml
│   ├── ws-sync-service.yaml
│   └── frontend.yaml
├── networking/
│   └── ingress.yaml             # NGINX Ingress for local
├── monitoring/
│   ├── prometheus/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml       # prometheus.yml scrape config
│   ├── grafana/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml       # dashboard JSON provisioning
│   └── otel-collector/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml       # otel-collector-config.yaml
└── kustomization.yaml
```

#### Dapr Annotations (per service deployment)

```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "task-api"
  dapr.io/app-port: "8000"
  dapr.io/app-protocol: "http"
  dapr.io/enable-metrics: "true"
  dapr.io/metrics-port: "9090"
  dapr.io/log-level: "info"
  dapr.io/sidecar-liveness-probe-delay-seconds: "10"
  dapr.io/sidecar-readiness-probe-delay-seconds: "5"
```

### 5.2 Cloud (AKS — Azure Kubernetes Service)

#### Cluster Configuration

```
AKS Cluster (Standard_D2s_v3, 3 nodes)
├── Namespace: todo-app
│   ├── task-api (2-5 replicas + HPA + Dapr sidecar)
│   ├── chat-api (1-3 replicas + HPA + Dapr sidecar)
│   ├── reminder-service (1 replica + Dapr sidecar)
│   ├── recurring-service (1 replica + Dapr sidecar)
│   ├── audit-service (1-2 replicas + Dapr sidecar)
│   ├── ws-sync-service (1-3 replicas + Dapr sidecar)
│   ├── frontend (2-4 replicas + HPA + Dapr sidecar)
│   └── Dapr Components (pubsub-kafka, statestore, secrets-azure-keyvault)
│
├── External Services
│   ├── Neon PostgreSQL (managed, external)
│   ├── Redpanda Cloud Kafka (managed, external)
│   └── Azure Key Vault (managed)
│
├── Namespace: monitoring
│   ├── Prometheus (1 replica + PVC)
│   ├── Grafana (1 replica + PVC)
│   └── OpenTelemetry Collector (1 replica)
│
├── Namespace: dapr-system
│   ├── dapr-operator
│   ├── dapr-sentry (mTLS enabled)
│   ├── dapr-sidecar-injector
│   └── dapr-placement
│
├── Ingress: NGINX Ingress Controller + cert-manager
│   ├── TLS via Let's Encrypt (cert-manager)
│   ├── / → frontend:3000
│   └── /ws/* → ws-sync-service:8005
│
└── Network Policies
    ├── Allow: frontend → task-api, chat-api (via Dapr)
    ├── Allow: task-api → postgresql, kafka
    ├── Allow: reminder-service → kafka, task-api (via Dapr)
    ├── Allow: recurring-service → kafka, task-api (via Dapr)
    ├── Allow: audit-service → kafka, postgresql
    ├── Allow: ws-sync-service → kafka
    └── Deny: all other inter-pod traffic
```

#### Production Kubernetes Manifests Structure

```
k8s/production/
├── namespaces/
│   ├── todo-app.yaml
│   └── monitoring.yaml
├── dapr/
│   ├── pubsub-kafka.yaml             # Redpanda Cloud, SASL/SCRAM
│   ├── statestore-postgresql.yaml     # Neon PostgreSQL
│   ├── secrets-azure-keyvault.yaml    # Azure Key Vault
│   └── subscriptions.yaml
├── services/
│   ├── task-api.yaml                  # + resource limits + PDB
│   ├── chat-api.yaml
│   ├── reminder-service.yaml
│   ├── recurring-service.yaml
│   ├── audit-service.yaml
│   ├── ws-sync-service.yaml
│   └── frontend.yaml
├── autoscaling/
│   ├── task-api-hpa.yaml              # min: 2, max: 5, CPU target: 70%
│   ├── chat-api-hpa.yaml             # min: 1, max: 3, CPU target: 70%
│   ├── frontend-hpa.yaml             # min: 2, max: 4, CPU target: 70%
│   └── ws-sync-hpa.yaml              # min: 1, max: 3, CPU target: 70%
├── networking/
│   ├── ingress.yaml                   # TLS, cert-manager annotations
│   ├── network-policies.yaml          # Restrict inter-pod traffic
│   └── cert-manager/
│       ├── cluster-issuer.yaml        # Let's Encrypt
│       └── certificate.yaml
├── disruption/
│   ├── task-api-pdb.yaml              # minAvailable: 1
│   ├── frontend-pdb.yaml             # minAvailable: 1
│   └── ws-sync-pdb.yaml              # minAvailable: 1
├── monitoring/
│   ├── prometheus/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── configmap.yaml
│   ├── grafana/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── configmap.yaml
│   └── otel-collector/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
└── kustomization.yaml
```

#### Resource Limits (Production)

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|------------|-----------|----------------|-------------|
| Task API | 250m | 500m | 256Mi | 512Mi |
| Chat API | 250m | 500m | 256Mi | 512Mi |
| Reminder Service | 100m | 250m | 128Mi | 256Mi |
| Recurring Service | 100m | 250m | 128Mi | 256Mi |
| Audit Service | 100m | 250m | 128Mi | 256Mi |
| WS Sync Service | 100m | 250m | 128Mi | 256Mi |
| Frontend | 250m | 500m | 256Mi | 512Mi |
| PostgreSQL (local) | 250m | 500m | 256Mi | 512Mi |
| Prometheus | 250m | 500m | 512Mi | 1Gi |
| Grafana | 100m | 250m | 128Mi | 256Mi |
| OTel Collector | 100m | 250m | 128Mi | 256Mi |

---

## 6. CI/CD Architecture

### 6.1 Pipeline Overview

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────────┐
│  PR Opened   │───▶│  Lint & Test  │───▶│  Build Images│───▶│  Deploy Stage │
│  (trigger)   │    │  (gate)       │    │  (on main)   │    │  (auto/manual)│
└─────────────┘    └──────────────┘    └──────────────┘    └───────────────┘
```

### 6.2 GitHub Actions Workflows

#### Workflow 1: `ci.yaml` — PR Gate

**Trigger**: Pull request to `main`

```
Jobs:
├── lint-backend
│   ├── ruff check backend/ services/
│   └── mypy backend/ services/
├── lint-frontend
│   ├── eslint frontend/
│   └── tsc --noEmit
├── test-backend
│   ├── pytest backend/tests/ --cov
│   └── pytest services/*/tests/ --cov
├── test-frontend
│   └── vitest run --coverage
└── docker-build-check
    └── docker build --target=builder (verify Dockerfiles compile)
```

#### Workflow 2: `cd.yaml` — Build, Push & Deploy

**Trigger**: Push to `main` (after PR merge)

```
Jobs:
├── build-and-push
│   ├── docker build -t ghcr.io/user/task-api:${SHA}
│   ├── docker build -t ghcr.io/user/chat-api:${SHA}
│   ├── docker build -t ghcr.io/user/reminder-service:${SHA}
│   ├── docker build -t ghcr.io/user/recurring-service:${SHA}
│   ├── docker build -t ghcr.io/user/audit-service:${SHA}
│   ├── docker build -t ghcr.io/user/ws-sync-service:${SHA}
│   ├── docker build -t ghcr.io/user/frontend:${SHA}
│   └── docker push (all images)
│
├── deploy-staging (auto)
│   ├── kustomize edit set image *:${SHA}
│   ├── kubectl apply -k k8s/production/ --namespace=staging
│   └── kubectl rollout status --timeout=120s
│
└── deploy-production (manual approval)
    ├── kustomize edit set image *:${SHA}
    ├── kubectl apply -k k8s/production/ --namespace=production
    └── kubectl rollout status --timeout=120s
```

### 6.3 Docker Images

| Image | Dockerfile | Base Image | Build Stages |
|-------|-----------|-----------|--------------|
| `task-api` | `docker/task-api.Dockerfile` | `python:3.12-slim` | deps → build → runtime |
| `chat-api` | `docker/chat-api.Dockerfile` | `python:3.12-slim` | deps → build → runtime |
| `reminder-service` | `docker/reminder-service.Dockerfile` | `python:3.12-slim` | deps → build → runtime |
| `recurring-service` | `docker/recurring-service.Dockerfile` | `python:3.12-slim` | deps → build → runtime |
| `audit-service` | `docker/audit-service.Dockerfile` | `python:3.12-slim` | deps → build → runtime |
| `ws-sync-service` | `docker/ws-sync-service.Dockerfile` | `python:3.12-slim` | deps → build → runtime |
| `frontend` | `docker/frontend.Dockerfile` | `node:22-alpine` | deps → build → runtime |

All images: non-root user, no `latest` tag, tagged with git commit SHA.

---

## 7. Monitoring Stack

### 7.1 Prometheus

**Scrape Targets**:

| Target | Port | Path | Interval |
|--------|------|------|----------|
| Task API | 9090 | `/metrics` (Dapr sidecar) | 15s |
| Chat API | 9090 | `/metrics` (Dapr sidecar) | 15s |
| Reminder Service | 9090 | `/metrics` (Dapr sidecar) | 15s |
| Recurring Service | 9090 | `/metrics` (Dapr sidecar) | 15s |
| Audit Service | 9090 | `/metrics` (Dapr sidecar) | 15s |
| WS Sync Service | 9090 | `/metrics` (Dapr sidecar) | 15s |
| Frontend | 9090 | `/metrics` (Dapr sidecar) | 15s |
| Strimzi Kafka | 9404 | `/metrics` | 30s |
| PostgreSQL (local) | 9187 | `/metrics` (postgres_exporter) | 30s |

**Custom Application Metrics** (exposed via `prometheus_client` in Python):

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | `method`, `endpoint`, `status_code`, `service` | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint`, `service` | Request latency |
| `kafka_events_published_total` | Counter | `topic`, `service` | Events published to Kafka |
| `kafka_events_consumed_total` | Counter | `topic`, `consumer_group`, `service` | Events consumed from Kafka |
| `kafka_events_failed_total` | Counter | `topic`, `consumer_group`, `service` | Failed event processing |
| `active_websocket_connections` | Gauge | `service` | Current WebSocket connections |
| `dapr_job_scheduled_total` | Counter | `service` | Dapr Jobs scheduled |
| `dapr_job_triggered_total` | Counter | `service` | Dapr Jobs fired |
| `tasks_created_total` | Counter | `service` | Tasks created |
| `tasks_completed_total` | Counter | `service` | Tasks completed |

### 7.2 Grafana Dashboards

| Dashboard | Panels |
|-----------|--------|
| **Service Overview** | Request rate, error rate (4xx/5xx), p50/p95/p99 latency per service |
| **Kafka Overview** | Consumer lag per topic/group, messages produced/consumed per second, partition distribution |
| **Task Metrics** | Tasks created/completed/deleted per minute, overdue task count, recurring generation rate |
| **Infrastructure** | Pod CPU/memory usage, pod restarts, node resource utilization |
| **Dapr** | Sidecar health, service invocation latency, pub/sub message delivery rate |

### 7.3 OpenTelemetry

**Instrumentation**:
- Python services: `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-httpx`
- Next.js frontend: `@opentelemetry/sdk-node` with HTTP instrumentation
- Trace context propagation via `traceparent` header (W3C Trace Context)

**Collector Pipeline**:
```
Services → OTel SDK → OTLP Exporter → OTel Collector → Prometheus (metrics)
                                                       → Grafana Tempo / Jaeger (traces)
```

### 7.4 Structured Logging

**Log Format** (all services):

```json
{
  "timestamp": "2026-02-22T10:30:00.123Z",
  "level": "INFO",
  "service": "task-api",
  "correlation_id": "uuid-v4",
  "user_id": "uuid-v4",
  "message": "Task created",
  "data": {
    "task_id": "uuid",
    "title": "Buy groceries"
  }
}
```

**Correlation ID Propagation**:
- Generated at ingress (or frontend Route Handler) if not present
- Passed via `X-Correlation-ID` header through all Dapr service invocations
- Included in all Kafka event envelopes
- Logged by every service on every request/event

---

## 8. Project Structure (Monorepo)

```
Phase-5/
├── frontend/                       # Next.js 16+ (App Router, TypeScript, Tailwind)
│   ├── src/
│   │   ├── app/                    # App Router pages
│   │   │   ├── (auth)/             # Auth pages (sign-in, sign-up)
│   │   │   ├── dashboard/          # Dashboard with tasks, tags, filter, search
│   │   │   ├── chat/               # Chatbot UI
│   │   │   └── api/                # Route Handlers (SSR Proxy → Dapr → services)
│   │   │       ├── tasks/          # Proxy to task-api
│   │   │       ├── tags/           # Proxy to task-api
│   │   │       ├── chat/           # Proxy to chat-api
│   │   │       └── auth/           # Proxy to task-api auth
│   │   ├── components/             # React components
│   │   │   ├── tasks/              # Task list, task card, task form
│   │   │   ├── tags/               # Tag manager, tag picker
│   │   │   ├── filters/            # Filter bar, sort controls
│   │   │   ├── search/             # Search input
│   │   │   ├── chat/               # Chat interface
│   │   │   └── ui/                 # Shared UI primitives
│   │   ├── lib/                    # Utilities
│   │   │   ├── api.ts              # Typed API client (calls Route Handlers)
│   │   │   ├── auth.ts             # JWT token management
│   │   │   ├── dapr.ts             # Dapr service invocation helper (server-side)
│   │   │   └── ws.ts               # WebSocket client
│   │   └── types/                  # TypeScript interfaces
│   ├── public/
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                        # Task API (FastAPI, Python)
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── config.py               # Settings (from Dapr secrets)
│   │   ├── database.py             # SQLModel engine + session
│   │   ├── models/                 # SQLModel entities
│   │   │   ├── task.py             # Task (extended: due_date, recurrence, reminder, search_vector)
│   │   │   ├── tag.py              # Tag, TaskTag
│   │   │   ├── user.py             # User (unchanged)
│   │   │   ├── audit.py            # AuditLog
│   │   │   └── conversation.py     # Conversation, Message (Phase III, unchanged)
│   │   ├── routers/                # FastAPI routers
│   │   │   ├── tasks.py            # Task CRUD + search/filter/sort
│   │   │   ├── tags.py             # Tag CRUD + task-tag association
│   │   │   ├── auth.py             # Auth endpoints (unchanged)
│   │   │   └── health.py           # Health + readiness probes
│   │   ├── dependencies/           # FastAPI dependencies
│   │   │   ├── auth.py             # get_current_user
│   │   │   └── database.py         # get_session
│   │   ├── events/                 # Event publishing
│   │   │   ├── publisher.py        # Dapr Pub/Sub publish helper
│   │   │   ├── schemas.py          # Event envelope + data schemas
│   │   │   └── topics.py           # Topic name constants
│   │   ├── search/                 # Full-text search
│   │   │   └── tsvector.py         # tsvector helper functions
│   │   ├── middleware/             # FastAPI middleware
│   │   │   ├── correlation.py      # Correlation ID injection
│   │   │   ├── logging.py          # Structured JSON logging
│   │   │   └── metrics.py          # Prometheus metrics
│   │   └── migrations/             # Alembic migrations
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── requirements.txt
│   └── pyproject.toml
│
├── services/
│   ├── chat-api/                   # Chat API Service (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   ├── chat.py         # Chat endpoint
│   │   │   │   └── health.py
│   │   │   ├── mcp/                # MCP tools (extended)
│   │   │   │   ├── tools.py        # add_task, list_tasks, update_task, add_tag, list_tags, search_tasks
│   │   │   │   └── schemas.py      # Tool parameter schemas
│   │   │   ├── agents/             # OpenAI Agents SDK
│   │   │   │   └── todo_agent.py
│   │   │   └── middleware/
│   │   │       ├── correlation.py
│   │   │       ├── logging.py
│   │   │       └── metrics.py
│   │   ├── tests/
│   │   └── requirements.txt
│   │
│   ├── reminder/                   # Reminder Service (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── handlers/           # Event handlers
│   │   │   │   ├── reminder_scheduled.py
│   │   │   │   ├── task_deleted.py
│   │   │   │   └── task_updated.py
│   │   │   ├── jobs/               # Dapr Jobs callbacks
│   │   │   │   └── reminder_triggered.py
│   │   │   ├── dapr_client.py      # Dapr Jobs API + Service Invocation helpers
│   │   │   ├── routers/
│   │   │   │   └── health.py
│   │   │   └── middleware/
│   │   │       ├── correlation.py
│   │   │       ├── logging.py
│   │   │       └── metrics.py
│   │   ├── tests/
│   │   └── requirements.txt
│   │
│   ├── recurring/                  # Recurring Task Service (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── handlers/
│   │   │   │   └── task_completed.py  # Compute next due date, create via Service Invocation
│   │   │   ├── recurrence.py       # Date computation logic
│   │   │   ├── dapr_client.py      # Dapr Service Invocation helper
│   │   │   ├── routers/
│   │   │   │   └── health.py
│   │   │   └── middleware/
│   │   │       ├── correlation.py
│   │   │       ├── logging.py
│   │   │       └── metrics.py
│   │   ├── tests/
│   │   └── requirements.txt
│   │
│   ├── audit/                      # Audit Service (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── models/
│   │   │   │   └── audit.py        # AuditLog SQLModel
│   │   │   ├── handlers/
│   │   │   │   └── audit_log.py    # Persist event to AuditLog table
│   │   │   ├── routers/
│   │   │   │   ├── audit.py        # Query audit logs
│   │   │   │   └── health.py
│   │   │   └── middleware/
│   │   │       ├── correlation.py
│   │   │       ├── logging.py
│   │   │       └── metrics.py
│   │   ├── tests/
│   │   └── requirements.txt
│   │
│   └── ws-sync/                    # WebSocket Sync Service (FastAPI)
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── handlers/           # Kafka event handlers
│       │   │   ├── task_events.py  # All task event types
│       │   │   └── reminder_events.py
│       │   ├── websocket/          # WebSocket management
│       │   │   ├── manager.py      # Connection manager (user_id → ws connections)
│       │   │   └── auth.py         # JWT validation for WS connections
│       │   ├── routers/
│       │   │   ├── ws.py           # WebSocket endpoint
│       │   │   └── health.py
│       │   └── middleware/
│       │       ├── correlation.py
│       │       ├── logging.py
│       │       └── metrics.py
│       ├── tests/
│       └── requirements.txt
│
├── docker/                         # Dockerfiles
│   ├── task-api.Dockerfile
│   ├── chat-api.Dockerfile
│   ├── reminder-service.Dockerfile
│   ├── recurring-service.Dockerfile
│   ├── audit-service.Dockerfile
│   ├── ws-sync-service.Dockerfile
│   └── frontend.Dockerfile
│
├── k8s/                            # Kubernetes manifests
│   ├── local/                      # Minikube
│   │   └── [see Section 5.1]
│   └── production/                 # AKS
│       └── [see Section 5.2]
│
├── dapr/                           # Dapr component definitions (shared reference)
│   └── components/
│       ├── pubsub-kafka.yaml
│       ├── statestore-postgresql.yaml
│       ├── secrets-kubernetes.yaml
│       ├── secrets-azure-keyvault.yaml
│       └── subscriptions.yaml
│
├── .github/
│   └── workflows/
│       ├── ci.yaml                 # PR gate: lint + test
│       └── cd.yaml                 # Build + push + deploy
│
├── monitoring/                     # Monitoring configs (reference)
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   │       ├── service-overview.json
│   │       ├── kafka-overview.json
│   │       ├── task-metrics.json
│   │       └── infrastructure.json
│   └── otel/
│       └── otel-collector-config.yaml
│
├── scripts/                        # Developer utilities
│   ├── setup-minikube.sh           # Full local setup script
│   ├── teardown-minikube.sh
│   └── port-forward.sh             # Expose services locally
│
├── specs/                          # SDD artifacts
│   └── 003-event-driven-cloud/
│       ├── spec.md
│       └── plan.md                 # This file
│
├── history/                        # PHRs and ADRs
│   ├── prompts/
│   │   └── 003-event-driven-cloud/
│   └── adr/
│
├── .specify/                       # SpecKit Plus
│   ├── memory/
│   │   └── constitution.md
│   └── templates/
│
├── CLAUDE.md
└── .gitignore
```

**Structure Decision**: Microservice monorepo. All services share the repository but are independently buildable and deployable via their own Dockerfiles. Shared Python utilities (event schemas, middleware) are duplicated per service to maintain independence — no shared library package.

---

## 9. Data Model

### 9.1 Database Schema (PostgreSQL)

The Task API and Audit Service share the same PostgreSQL database but use separate tables. All other services are stateless (relying on Kafka events and Dapr state store).

**Database**: `todo_app` (local) / Neon serverless (production)

#### Tables

| Table | Owner Service | Description |
|-------|--------------|-------------|
| `users` | Task API | User accounts (Phase II, unchanged) |
| `tasks` | Task API | Tasks with extended fields |
| `tags` | Task API | User-scoped tags |
| `task_tags` | Task API | Many-to-many junction |
| `audit_logs` | Audit Service | Immutable event log |
| `conversations` | Chat API | Chat conversations (Phase III) |
| `messages` | Chat API | Chat messages (Phase III) |
| `dapr_state` | Dapr | Dapr state store table |
| `dapr_metadata` | Dapr | Dapr metadata table |

Full entity definitions are in spec Section 10 (Data Model Extensions).

### 9.2 Migration Strategy

- Use Alembic for schema migrations
- Each service that owns tables runs its own Alembic migration set
- Migrations are idempotent and backward-compatible
- Production migrations run as a Kubernetes Job before deployment

---

## 10. Cross-Cutting Concerns

### 10.1 Error Handling

All services return errors in a consistent format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "VALIDATION_ERROR",
  "correlation_id": "uuid-v4"
}
```

| HTTP Status | Usage |
|-------------|-------|
| 400 | Malformed request |
| 401 | Missing or invalid JWT |
| 404 | Resource not found (or belongs to another user) |
| 409 | Conflict (duplicate tag, etc.) |
| 422 | Validation error (Pydantic) |
| 500 | Internal server error |
| 503 | Service unavailable (Dapr sidecar not ready, DB down) |

### 10.2 Idempotency

- All Kafka consumers track processed `event_id` values via Dapr state store
- Before processing an event, check if `event_id` exists in state store
- If it exists, skip processing (return success to Kafka)
- If it doesn't exist, process event, then store `event_id`

### 10.3 Dead-Letter Handling

- Events that fail after 3 retries (exponential backoff: 1s, 5s, 25s) are published to `todo.task.dlq`
- Dead-letter events include the original event plus error metadata
- A future admin endpoint can replay dead-letter events

### 10.4 Security

- JWT auth on all API endpoints (except health/readiness)
- User data isolation: `WHERE user_id = <authenticated_user_id>` on all queries
- 404 instead of 403 for other users' resources
- CORS with explicit origin allowlist
- Kafka SASL/SCRAM in production
- Non-root container users
- Network policies in production K8s
- Dapr mTLS between sidecars (production)

---

## 11. Complexity Tracking

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|-------------------------------------|
| 6 microservices (vs spec's 4) | User requirement: Chat API, Audit Service, WS Sync as separate services | Spec had audit in Task API and no WS Sync; user explicitly requested separation |
| Strimzi for local Kafka | Full Kafka compatibility in Minikube | Docker-compose Redpanda simpler but doesn't test K8s Kafka operators |
| PostgreSQL state store (not Redis) | User requirement: `state.postgresql` | Redis simpler but user explicitly requested PostgreSQL |
| WebSocket Sync Service | User requirement for real-time updates | Spec listed WebSocket as out-of-scope; user overrides |

---

## 12. Spec Deviations

The following plan decisions deviate from the original spec. These are driven by the user's architecture requirements.

| Deviation | Spec Says | Plan Says | Rationale |
|-----------|-----------|-----------|-----------|
| Audit Service | Task API self-consumes `todo.audit.log` (spec §7.2) | Dedicated Audit Service | User explicitly requested Audit Service as a separate microservice |
| WebSocket Sync Service | Out-of-scope (spec §5) | In-scope as WS Sync Service | User explicitly requested WebSocket Sync Service |
| Chat API | Part of backend or single service | Separate Chat API microservice | User explicitly requested Chat API as separate service |
| State Store | Redis (`state.redis`) in spec §9.2 | PostgreSQL (`state.postgresql`) | User explicitly requested `state.postgresql` |
| Local Kafka | "Local Redpanda" in spec §17.1 | Strimzi Kafka operator in Minikube | User explicitly requested Strimzi for local |

---

## Follow-ups & Risks

1. **ADR Suggestion**: The addition of 3 services not in the original spec (Chat API separation, Audit Service extraction, WebSocket Sync Service) is an architecturally significant decision. Consider documenting: "Architectural decision detected: Expand from 4 to 6 microservices — Document reasoning and tradeoffs? Run `/sp.adr microservice-expansion`"

2. **Risk — Strimzi Complexity**: Strimzi Kafka operator in Minikube is resource-heavy (ZooKeeper + Kafka broker). May require Minikube with 8GB+ RAM. Mitigation: document minimum resources in `scripts/setup-minikube.sh`.

3. **Risk — WebSocket + Kubernetes**: WebSocket connections are stateful and complicate horizontal scaling of WS Sync Service. Mitigation: use sticky sessions at ingress level and Kafka consumer groups to partition users across instances.
