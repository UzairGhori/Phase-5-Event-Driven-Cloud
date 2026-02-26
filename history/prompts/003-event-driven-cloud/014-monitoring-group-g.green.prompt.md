---
id: 014
title: Monitoring and Logging GROUP G
stage: green
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: uzair
command: sp.implement
labels: ["monitoring", "prometheus", "grafana", "otel", "alerting", "group-g"]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/middleware/metrics.py
  - monitoring/prometheus/prometheus.yml
  - monitoring/prometheus/alerts.yml
  - monitoring/grafana/dashboards/dapr.json
  - k8s/local/monitoring/prometheus/configmap.yaml
  - k8s/local/monitoring/grafana/configmap.yaml
  - k8s/local/monitoring/grafana/deployment.yaml
  - k8s/local/monitoring/grafana/dashboards-configmap.yaml
  - k8s/local/kustomization.yaml
  - scripts/setup-monitoring.sh
  - specs/003-event-driven-cloud/tasks.md
tests:
  - none
---

## Prompt

Execute GROUP G tasks (Monitoring & Logging).

Implement:
- Option A: Prometheus + Grafana
- Option B (Azure): Azure Monitor + Log Analytics

Requirements: Kafka metrics, Dapr metrics, API latency, Pod health, Event lag monitoring
Generate: Helm installation commands, Alert rule examples, Dashboard configuration summary

## Response snapshot

Implemented GROUP G — Monitoring & Logging across all 7 tasks (T-G001–T-G007):

**T-G001 (Logging)**: Already done — CorrelationMiddleware + JSONFormatter + RequestLoggingMiddleware in `backend/app/middleware/`.

**T-G002 (Metrics)**: Added 5 missing metrics to reach all 10 per plan §7.1: `kafka_events_consumed_total`, `kafka_events_failed_total`, `active_websocket_connections`, `dapr_job_scheduled_total`, `dapr_job_triggered_total`.

**T-G003 (Health probes)**: Already done — All 7 services have `/api/health` + `/api/ready` with dependency checks.

**T-G004 (OTel tracing)**: OTel Collector pipeline configured (OTLP → Prometheus metrics + stdout traces).

**T-G005 (Prometheus)**: Added 2 missing scrape targets (Strimzi Kafka port 9404 @ 30s, PostgreSQL exporter port 9187 @ 30s). Created `monitoring/prometheus/alerts.yml` with 10 alert rules across 4 groups:
- api_alerts: HighErrorRate, HighP95Latency, HighP99Latency
- kafka_alerts: KafkaConsumerLagHigh, KafkaPublishFailures
- pod_health_alerts: PodRestartLoop, PodNotReady, HighCPUUsage, HighMemoryUsage
- dapr_alerts: DaprSidecarUnhealthy, DaprInvocationErrors

**T-G006 (Grafana)**: Created 5th Dapr dashboard. Fixed dashboard provisioning (separate dashboards-configmap.yaml with all 5 JSON dashboards, proper volume mounts in Grafana deployment).

**T-G007 (OTel Collector)**: Already done — deployment, service, configmap with OTLP→Prometheus+logging pipeline.

**New: `scripts/setup-monitoring.sh`** — 3-mode monitoring setup:
- `--manifests` (default): kubectl apply from k8s/local/monitoring/
- `--helm`: Full Helm chart installation (kube-prometheus-stack, grafana, opentelemetry-collector)
- `--azure`: Azure Monitor + Log Analytics workspace + Container Insights

## Outcome

- ✅ Impact: Full observability stack with Prometheus (4 scrape targets), Grafana (5 dashboards), OTel Collector, 10 alert rules
- 🧪 Tests: No automated tests (infrastructure configuration)
- 📁 Files: 7 modified, 4 created
- 🔁 Next prompts: All groups B–G complete; only GROUP A (Advanced Features) remains
- 🧠 Reflection: Most GROUP G artifacts pre-existed; key gaps were missing metrics, scrape targets, alert rules, and Dapr dashboard

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Validate Prometheus config with promtool check config
