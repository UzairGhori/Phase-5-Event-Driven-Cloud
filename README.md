# Phase V — Advanced Event-Driven Cloud Deployment

A production-grade microservices application built with FastAPI, Next.js, Kafka (via Dapr), and Kubernetes. Features event-driven architecture, real-time WebSocket updates, and full observability.

## Architecture

```
                              ┌─────────────────────────────────────────────────┐
                              │               Kubernetes Cluster                │
                              │                                                 │
  ┌──────────┐   HTTPS/WSS   │  ┌─────────────────────────────────────────┐    │
  │  Browser  │──────────────▶│  │        NGINX Ingress (TLS)             │    │
  └──────────┘                │  │   /        → frontend:3000              │    │
                              │  │   /api     → task-api:8000              │    │
                              │  │   /api/chat→ chat-api:8001              │    │
                              │  │   /ws      → ws-sync:8005               │    │
                              │  └──────────────┬──────────────────────────┘    │
                              │                 │                               │
                              │  ┌──────────────▼──────────────────────────┐    │
                              │  │         Application Services             │    │
                              │  │                                          │    │
                              │  │  ┌───────────┐  ┌───────────┐           │    │
                              │  │  │ Frontend  │  │ Chat API  │           │    │
                              │  │  │ Next.js   │  │ :8001     │           │    │
                              │  │  │ :3000     │  │ +Dapr     │           │    │
                              │  │  │ +Dapr     │  └───────────┘           │    │
                              │  │  └───────────┘                          │    │
                              │  │                                          │    │
                              │  │  ┌──────────────────────────────────┐    │    │
                              │  │  │         Task API :8000           │    │    │
                              │  │  │         (Primary Service)        │    │    │
                              │  │  │         +Dapr Sidecar            │    │    │
                              │  │  └──────────┬───────────────────────┘    │    │
                              │  │             │ Publishes Events           │    │
                              │  │             ▼                            │    │
                              │  │  ┌──────────────────────────────────┐    │    │
                              │  │  │     Kafka (Dapr Pub/Sub)         │    │    │
                              │  │  │     8 Topics                     │    │    │
                              │  │  └──┬────┬────┬────┬────────────────┘    │    │
                              │  │     │    │    │    │                     │    │
                              │  │     ▼    ▼    ▼    ▼                     │    │
                              │  │  ┌────┐┌────┐┌────┐┌────────┐           │    │
                              │  │  │Rem.││Rec.││Aud.││WS-Sync │           │    │
                              │  │  │8002││8003││8004││  8005   │           │    │
                              │  │  └────┘└────┘└────┘└────────┘           │    │
                              │  └──────────────────────────────────────────┘    │
                              │                                                 │
                              │  ┌──────────────────────────────────────────┐    │
                              │  │         Monitoring (namespace)            │    │
                              │  │  Prometheus │ Grafana │ OTel Collector    │    │
                              │  └──────────────────────────────────────────┘    │
                              │                                                 │
                              │  ┌──────────────────────────────────────────┐    │
                              │  │         Data Layer                        │    │
                              │  │  PostgreSQL (Neon prod / local dev)       │    │
                              │  └──────────────────────────────────────────┘    │
                              └─────────────────────────────────────────────────┘
```

## Services

| Service | Port | Tech | Role |
|---------|------|------|------|
| **task-api** | 8000 | FastAPI | Primary CRUD, event publisher |
| **chat-api** | 8001 | FastAPI | AI chatbot (OpenAI Agents SDK) |
| **reminder** | 8002 | FastAPI | Dapr Jobs scheduling |
| **recurring** | 8003 | FastAPI | Recurrence date computation |
| **audit** | 8004 | FastAPI | Audit trail persistence |
| **ws-sync** | 8005 | FastAPI | Real-time WebSocket push |
| **frontend** | 3000 | Next.js | SSR UI with Dapr service invocation |

## Event-Driven Architecture

```
Task API (Publisher)                     Consumer Services
─────────────────                        ─────────────────
POST /api/tasks ──┐
                  ├──▶ todo.task.created ──▶ WS-Sync, Audit
PUT  /api/tasks ──┤
                  ├──▶ todo.task.updated ──▶ WS-Sync, Audit, Reminder
PATCH complete ───┤
                  ├──▶ todo.task.completed ─▶ WS-Sync, Audit, Recurring
DELETE /api/tasks ┤
                  ├──▶ todo.task.deleted ──▶ WS-Sync, Audit, Reminder
                  ├──▶ todo.audit.log ─────▶ Audit
                  ├──▶ todo.reminder.scheduled ──▶ Reminder
                  └──▶ todo.reminder.triggered ──▶ WS-Sync
```

**8 Kafka Topics** via Dapr Pub/Sub — all events use `EventEnvelope` with correlation ID propagation.

## Dapr Components

| Component | Type | Local | Production |
|-----------|------|-------|------------|
| pubsub-kafka | pubsub.kafka | Strimzi (no auth) | Redpanda Cloud (SASL/SCRAM) |
| statestore | state.postgresql | Local PG | Neon PostgreSQL |
| secrets-store | secretstores.kubernetes / azure.keyvault | K8s Secrets | Azure Key Vault |

## Monitoring Stack

### Prometheus (4 Scrape Targets)
| Target | Port | Interval |
|--------|------|----------|
| Dapr sidecars | 9090 | 15s |
| App /metrics | varies | 15s |
| Strimzi Kafka | 9404 | 30s |
| PostgreSQL exporter | 9187 | 30s |

### 10 Alert Rules
- **API**: HighErrorRate (>5%), HighP95Latency (>1s), HighP99Latency (>3s)
- **Kafka**: ConsumerLagHigh (>1000), PublishFailures
- **Pods**: RestartLoop (>3/15m), NotReady (5m), HighCPU (>80%), HighMemory (>85%)
- **Dapr**: SidecarUnhealthy, InvocationErrors

### 5 Grafana Dashboards
Service Overview | Kafka Overview | Task Metrics | Infrastructure | Dapr

### 10 Custom Prometheus Metrics
`http_requests_total`, `http_request_duration_seconds`, `kafka_events_published_total`, `kafka_events_consumed_total`, `kafka_events_failed_total`, `active_websocket_connections`, `dapr_job_scheduled_total`, `dapr_job_triggered_total`, `tasks_created_total`, `tasks_completed_total`

## Quick Start

### Local (Minikube)
```bash
# One-command setup
bash scripts/setup-minikube.sh

# Or step-by-step
kubectl apply -k k8s/local/

# Access
bash scripts/port-forward.sh
# App: http://localhost:3000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### Production (AKS)
```bash
# Set required secrets
export NEON_CONNECTION_STRING="postgres://..."
export JWT_SECRET_KEY="your-secret"
export OPENAI_API_KEY="sk-..."
export REDPANDA_BROKERS="..."
export REDPANDA_USERNAME="..."
export REDPANDA_PASSWORD="..."

# Deploy
bash scripts/deploy-aks.sh
```

### Monitoring
```bash
# Via Kubernetes manifests (default)
bash scripts/setup-monitoring.sh

# Via Helm charts
bash scripts/setup-monitoring.sh --helm

# Azure Monitor (AKS only)
bash scripts/setup-monitoring.sh --azure
```

## CI/CD Pipeline

**`.github/workflows/deploy.yml`** — Unified pipeline:

```
PR opened ──▶ Lint + Test ──▶ Docker Build Check
                                    │
Push to main ──▶ Lint + Test ──▶ Build & Push (ghcr.io) ──▶ Deploy Staging (auto)
                                                                    │
                                                            Deploy Production (manual)
```

- 7 Docker images built in parallel (matrix)
- Docker Buildx with GHA cache
- Multi-target: AKS (default), GKE, Minikube via `DEPLOY_TARGET`
- Concurrency control, coverage artifacts

## Project Structure

```
Phase-5/
├── backend/app/                     # Task API (primary service)
│   ├── events/                      #   Event schemas, publisher, topics
│   ├── middleware/                   #   Correlation, logging, metrics
│   ├── models/                      #   SQLModel entities
│   └── routers/                     #   API endpoints + health probes
├── services/
│   ├── audit/                       # Audit Service (event consumer)
│   ├── chat-api/                    # Chat API (OpenAI agent)
│   ├── recurring/                   # Recurring Task Service
│   ├── reminder/                    # Reminder Service (Dapr Jobs)
│   └── ws-sync/                     # WebSocket Sync Service
├── frontend/                        # Next.js frontend
├── docker/                          # 7 Dockerfiles (multi-stage)
├── dapr/components/                 # Dapr component YAMLs
├── k8s/
│   ├── local/                       # Minikube manifests
│   │   ├── namespaces/              #   3 namespaces
│   │   ├── infrastructure/          #   PostgreSQL, Strimzi Kafka
│   │   ├── dapr/                    #   Dapr components (local)
│   │   ├── services/                #   7 service deployments
│   │   ├── networking/              #   Ingress
│   │   ├── monitoring/              #   Prometheus, Grafana, OTel
│   │   └── kustomization.yaml
│   └── production/                  # AKS manifests
│       ├── namespaces/              #   2 namespaces
│       ├── dapr/                    #   Dapr components (production)
│       ├── services/                #   7 service deployments
│       ├── autoscaling/             #   4 HPAs
│       ├── disruption/              #   3 PDBs
│       ├── networking/              #   Ingress, TLS, Network Policies
│       └── kustomization.yaml
├── monitoring/
│   ├── prometheus/                  # Scrape config + alert rules
│   ├── grafana/dashboards/          # 5 dashboard JSON files
│   └── otel/                        # Collector pipeline config
├── scripts/
│   ├── setup-minikube.sh            # Local cluster setup
│   ├── teardown-minikube.sh         # Local cluster teardown
│   ├── port-forward.sh              # Local port forwarding
│   ├── deploy-aks.sh                # AKS provisioning + deploy
│   └── setup-monitoring.sh          # Monitoring stack setup
├── .github/workflows/
│   ├── ci.yaml                      # PR gate (lint + test)
│   ├── cd.yaml                      # Build + push + deploy
│   └── deploy.yml                   # Unified CI/CD pipeline
└── specs/003-event-driven-cloud/
    ├── spec.md                      # Feature specification
    ├── plan.md                      # Architecture plan
    └── tasks.md                     # 66 tasks (35 done: B-G)
```

## Task Progress

| Group | Tasks | Done | Status |
|-------|-------|------|--------|
| A — Advanced Features | 31 | 0 | Pending |
| B — Kafka Integration | 4 | 4 | Complete |
| C — Dapr Integration | 6 | 6 | Complete |
| D — Local Deployment | 9 | 9 | Complete |
| E — Cloud Deployment | 7 | 7 | Complete |
| F — CI/CD | 2 | 2 | Complete |
| G — Monitoring | 7 | 7 | Complete |
| **Total** | **66** | **35** | **53%** |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLModel, Pydantic |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 (Neon prod, local dev) |
| Messaging | Apache Kafka via Dapr Pub/Sub |
| Runtime | Dapr 1.14.4 (sidecar pattern) |
| Container | Docker (multi-stage, non-root) |
| Orchestration | Kubernetes (Minikube local, AKS/GKE prod) |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus, Grafana, OpenTelemetry |
| Ingress | NGINX Ingress Controller + cert-manager |
