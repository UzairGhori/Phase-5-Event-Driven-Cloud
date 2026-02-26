---
id: 003
title: Architectural Plan Generation for Phase V
stage: plan
date: 2026-02-22
surface: project
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: architect
command: /sp.plan
labels: [plan, architecture, microservices, dapr, kafka, kubernetes, ci-cd, monitoring]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - path: specs/003-event-driven-cloud/plan.md
    action: created
tests:
  - N/A
---

## Prompt

/sp.plan Generate speckit.plan for Phase V based strictly on speckit.specify.

Architecture Requirements:

Microservices:
- Chat API (FastAPI + MCP tools)
- Recurring Task Service
- Notification Service
- Audit Service
- WebSocket Sync Service

Infrastructure:
- Kubernetes cluster
- Dapr sidecars per service
- Kafka cluster (Strimzi for local, Redpanda Cloud for production)
- Neon Postgres
- Kubernetes Secrets

Define:
- Service responsibilities
- API contracts
- Event publishing/subscription matrix
- Dapr components:
    - pubsub.kafka
    - state.postgresql
    - secretstores.kubernetes
    - Jobs API usage
- Deployment topology for:
    1. Minikube
    2. Cloud (AKS/GKE/OKE)
- CI/CD architecture
- Monitoring stack (Prometheus + Grafana or Azure Monitor)

Do not write tasks.
Only generate speckit.plan.

## Response snapshot

Generated comprehensive architectural plan at `specs/003-event-driven-cloud/plan.md` covering 12 major sections:

1. **Service Architecture** — 6 microservices (Task API, Chat API, Reminder Service, Recurring Task Service, Audit Service, WebSocket Sync Service) + Frontend, with full responsibility matrix.
2. **API Contracts** — Complete endpoint definitions for all 6 services plus health/readiness probes.
3. **Event Publishing/Subscription Matrix** — 8 Kafka topics, publisher matrix (2 producers), subscriber matrix (4 consumer groups, 11 subscriptions).
4. **Dapr Components** — `pubsub.kafka`, `state.postgresql`, `secretstores.kubernetes` / `secretstores.azure.keyvault`, full subscription YAML, Jobs API usage patterns, Service Invocation patterns.
5. **Deployment Topology** — Minikube (local) with Strimzi Kafka + local PostgreSQL, AKS (production) with Redpanda Cloud + Neon + Azure Key Vault. Full manifest directory structures for both.
6. **CI/CD Architecture** — 2 GitHub Actions workflows (ci.yaml for PR gate, cd.yaml for build/push/deploy), 7 Docker images with multi-stage builds.
7. **Monitoring Stack** — Prometheus scrape targets + 10 custom metrics, 5 Grafana dashboards, OpenTelemetry tracing pipeline, structured JSON logging format.
8. **Project Structure** — Full monorepo directory tree with all source files mapped.
9. **Data Model** — Database ownership per service, migration strategy.
10. **Cross-Cutting Concerns** — Error format, idempotency, dead-letter handling, security.
11. **Complexity Tracking** — 4 justified deviations from simpler alternatives.
12. **Spec Deviations** — 5 documented deviations from original spec, all driven by user requirements.

Notable deviations from spec: Audit Service extracted from Task API self-consumption, WebSocket Sync added (was out-of-scope), Chat API separated, state store changed from Redis to PostgreSQL, local Kafka changed from Redpanda to Strimzi.

## Outcome

- Impact: Full architectural plan generated covering all user-requested dimensions (services, contracts, events, Dapr, deployment, CI/CD, monitoring)
- Tests: N/A (plan artifact, no code)
- Files: 1 created (specs/003-event-driven-cloud/plan.md)
- Next prompts: `/sp.tasks` to break plan into dependency-ordered implementation tasks; `/sp.adr microservice-expansion` to document the 4→6 service expansion decision
- Reflection: User requirements expanded scope beyond original spec in 3 areas (Audit Service separation, WebSocket Sync, Chat API separation). All deviations documented in Section 12.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review pending
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
