# Phase V — Submission Checklist

## Validation Date: 2026-02-25

---

## 1. Event-Driven Architecture

- [x] **Event schemas defined** — `EventEnvelope` + 8 typed data schemas (`backend/app/events/schemas.py`)
- [x] **8 Kafka topics defined** — `backend/app/events/topics.py` (task.created/updated/completed/deleted, audit.log, reminder.scheduled/triggered + 1 DLQ)
- [x] **Publisher with retry** — `backend/app/events/publisher.py` (exponential backoff, DLQ fallback)
- [x] **Events wired into CRUD** — Task API publishes on create/update/complete/delete
- [x] **Schemas duplicated per service** — 4 consumer services each have their own copy
- [x] **Correlation ID propagation** — Generated at ingress, passed through all events

## 2. Dapr Abstraction Layer

- [x] **Pub/Sub Kafka (local)** — `dapr/components/pubsub-kafka-local.yaml` (Strimzi, no auth)
- [x] **Pub/Sub Kafka (production)** — `dapr/components/pubsub-kafka-production.yaml` (Redpanda, SASL/SCRAM)
- [x] **State store (PostgreSQL)** — `dapr/components/statestore-postgresql.yaml`
- [x] **Secrets store (K8s)** — `dapr/components/secrets-kubernetes.yaml`
- [x] **Secrets store (Azure KV)** — `dapr/components/secrets-azure-keyvault.yaml`
- [x] **Subscriptions** — `dapr/components/subscriptions.yaml` (10 subscriptions across 4 services)
- [x] **Local K8s manifests** — 4 files in `k8s/local/dapr/`
- [x] **Production K8s manifests** — 4 files in `k8s/production/dapr/`

## 3. Local Deployment (Minikube)

- [x] **7 Dockerfiles** — Multi-stage, non-root, Python 3.12-slim / Node 22-alpine
- [x] **3 namespaces** — todo-app, kafka, monitoring
- [x] **PostgreSQL** — Deployment + Service + PVC + ConfigMap (init.sql)
- [x] **Strimzi Kafka** — KafkaCluster CR (KRaft, 1 broker) + 8 KafkaTopic CRs
- [x] **Kubernetes Secrets** — db-secrets, jwt-secrets, openai-secrets
- [x] **7 service deployments** — Each with Dapr annotations, probes, env vars
- [x] **Ingress** — NGINX routing (/, /api, /ws)
- [x] **Kustomization** — `kubectl apply -k k8s/local/` deploys everything
- [x] **Setup script** — `scripts/setup-minikube.sh`
- [x] **Teardown script** — `scripts/teardown-minikube.sh`
- [x] **Port-forward script** — `scripts/port-forward.sh`

## 4. Cloud Deployment (AKS)

- [x] **2 namespaces** — todo-app, monitoring
- [x] **7 service deployments** — Production resource limits per plan §5.2
- [x] **All services have Dapr annotations** — Including frontend
- [x] **4 HPAs** — task-api (2-5), chat-api (1-3), frontend (2-4), ws-sync (1-3) @ 70% CPU
- [x] **3 PDBs** — task-api, frontend, ws-sync (minAvailable: 1)
- [x] **Ingress with TLS** — NGINX + cert-manager (Let's Encrypt)
- [x] **Network Policies** — Default deny + explicit allows per service
- [x] **Kustomization** — `kubectl apply -k k8s/production/` deploys everything
- [x] **Deploy script (AKS)** — `scripts/deploy-aks.sh` (8-phase provisioning)
- [x] **Deploy script (DO)** — `scripts/deploy-digitalocean.sh` (9-phase DOKS provisioning)

## 5. CI/CD Pipeline

- [x] **CI workflow (PR gate)** — `.github/workflows/ci.yaml` (lint + test + Docker build check)
- [x] **CD workflow** — `.github/workflows/cd.yaml` (build + push + staging auto + production manual)
- [x] **Unified pipeline** — `.github/workflows/deploy.yml` (test → build → push → deploy)
- [x] **Multi-target support** — AKS, GKE, DigitalOcean, Minikube via `DEPLOY_TARGET` env var
- [x] **Docker Buildx** — With GHA layer cache
- [x] **Concurrency control** — Cancels in-flight runs for same branch
- [x] **Coverage artifacts** — Backend (pytest-cov) + Frontend (vitest coverage)
- [x] **Secrets via GitHub Environments** — No hardcoded credentials

## 6. Monitoring & Observability

- [x] **Structured JSON logging** — `backend/app/middleware/logging.py` (timestamp, level, service, correlation_id, message)
- [x] **Correlation ID middleware** — `backend/app/middleware/correlation.py` (X-Correlation-ID header)
- [x] **10/10 Prometheus metrics** — All custom metrics from plan §7.1
- [x] **Health probes on all services** — `/api/health` (liveness) + `/api/ready` (readiness with dependency checks)
- [x] **Prometheus scrape config** — 4 targets (Dapr sidecars, app metrics, Strimzi Kafka, PostgreSQL)
- [x] **10 alert rules** — API (3), Kafka (2), Pods (4), Dapr (1)
- [x] **5 Grafana dashboards** — Service Overview, Kafka, Task Metrics, Infrastructure, Dapr
- [x] **OTel Collector** — OTLP → Prometheus (metrics) + stdout (traces)
- [x] **Setup script** — `scripts/setup-monitoring.sh` (--manifests, --helm, --azure)

## 7. Documentation

- [x] **README.md** — Architecture diagram, service table, quick start, project structure
- [x] **DEPLOYMENT.md** — Full deployment guide (Minikube, AKS, GKE, Monitoring, Troubleshooting)
- [x] **SUBMISSION_CHECKLIST.md** — This file

## 8. Artifact Count

| Category | Count |
|----------|-------|
| Python microservices | 6 |
| Next.js frontend | 1 |
| Dockerfiles | 7 |
| Dapr components | 6 |
| Dapr subscriptions | 10 |
| Kafka topics | 8 |
| K8s manifests (local) | 24 |
| K8s manifests (production) | 21 |
| GitHub Actions workflows | 3 |
| Prometheus alert rules | 10 |
| Grafana dashboards | 5 |
| Custom Prometheus metrics | 10 |
| Shell scripts | 6 |
| Spec artifacts | 3 (spec, plan, tasks) |
| PHR records | 15 |
| **Total files** | **~130+** |

## 9. Task Completion Summary

| Group | Tasks | Done | Status |
|-------|-------|------|--------|
| B — Kafka Integration | 4 | 4 | COMPLETE |
| C — Dapr Integration | 6 | 6 | COMPLETE |
| D — Local Deployment | 9 | 9 | COMPLETE |
| E — Cloud Deployment | 7 | 7 | COMPLETE |
| F — CI/CD | 2 | 2 | COMPLETE |
| G — Monitoring | 7 | 7 | COMPLETE |
| **Infrastructure Total** | **35** | **35** | **100%** |
| A — Advanced Features | 31 | 0 | Not in scope (infrastructure-first) |
| **Grand Total** | **66** | **35** | **53%** |

## 10. Verification Commands

```bash
# Validate all local manifests
kubectl apply -k k8s/local/ --dry-run=client


# Validate all production manifests
kubectl apply -k k8s/production/ --dry-run=client

# Check Dockerfile syntax
for f in docker/*.Dockerfile; do docker build --check -f "$f" . 2>/dev/null; done

# Verify GitHub Actions YAML
# (use actionlint if installed)
actionlint .github/workflows/*.yml .github/workflows/*.yaml

# Verify Prometheus config
# (use promtool if installed)
promtool check config monitoring/prometheus/prometheus.yml
promtool check rules monitoring/prometheus/alerts.yml
```

---

**Validated by**: Claude Opus 4.6 (automated audit)
**Date**: 2026-02-25
**Status**: All infrastructure groups (B-G) verified complete. 35/35 tasks done. 130+ artifacts generated.
