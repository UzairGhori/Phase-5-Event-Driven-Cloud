---
id: "008"
title: Frontend, OpenTelemetry, and Monitoring Implementation
stage: green
date: 2026-02-25
surface: project
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: architect
command: continue
labels: [frontend, otel, monitoring, T-A027, T-A028, T-A029, T-A030, T-A031, T-G004, T-G007]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: ""
  adr: ""
  pr: ""
files:
  - frontend/package.json
  - frontend/tsconfig.json
  - frontend/next.config.ts
  - frontend/tailwind.config.ts
  - frontend/postcss.config.mjs
  - frontend/src/app/globals.css
  - frontend/src/app/layout.tsx
  - frontend/src/app/page.tsx
  - frontend/src/app/login/page.tsx
  - frontend/src/app/signup/page.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/types/index.ts
  - frontend/src/lib/dapr.ts
  - frontend/src/lib/ws.ts
  - frontend/src/app/api/tasks/route.ts
  - frontend/src/app/api/tasks/[taskId]/route.ts
  - frontend/src/app/api/tasks/[taskId]/complete/route.ts
  - frontend/src/app/api/tasks/[taskId]/tags/route.ts
  - frontend/src/app/api/tasks/[taskId]/tags/[tagId]/route.ts
  - frontend/src/app/api/tasks/overdue/route.ts
  - frontend/src/app/api/tags/route.ts
  - frontend/src/app/api/tags/[tagId]/route.ts
  - frontend/src/app/api/auth/signup/route.ts
  - frontend/src/app/api/auth/token/route.ts
  - frontend/src/app/api/auth/me/route.ts
  - frontend/src/app/api/chat/route.ts
  - frontend/src/components/tags/tag-badge.tsx
  - frontend/src/components/tags/tag-list.tsx
  - frontend/src/components/tags/tag-create-dialog.tsx
  - frontend/src/components/tags/tag-picker.tsx
  - frontend/src/components/search/search-input.tsx
  - frontend/src/components/filters/filter-bar.tsx
  - frontend/src/components/filters/sort-controls.tsx
  - frontend/src/components/ui/pagination.tsx
  - frontend/src/components/tasks/task-form.tsx
  - backend/app/tracing.py
  - services/reminder/app/tracing.py
  - services/recurring/app/tracing.py
  - services/audit/app/tracing.py
  - services/ws-sync/app/tracing.py
  - services/chat-api/app/tracing.py
  - k8s/local/monitoring/otel-collector/deployment.yaml
  - k8s/local/monitoring/otel-collector/service.yaml
  - k8s/local/monitoring/otel-collector/configmap.yaml
  - monitoring/otel/otel-collector-config.yaml
  - monitoring/grafana/dashboards/kafka-overview.json
  - monitoring/grafana/dashboards/task-metrics.json
  - monitoring/grafana/dashboards/infrastructure.json
tests:
  - "N/A — greenfield implementation"
---

## Prompt

continue (continuation from previous session that hit context limits). Implement all remaining tasks: T-A027–A031 (frontend), T-G004 (OpenTelemetry tracing), T-G007 (OTel Collector K8s manifests), and missing Grafana dashboards.

## Response snapshot

Implemented all remaining 7 tasks across frontend, OpenTelemetry, and monitoring:

**T-A027 (SSR Proxy)**: Created 16 Next.js Route Handler files proxying all backend endpoints (tasks, tags, auth, chat) through Dapr service invocation helper. Foundation files: package.json, tsconfig, tailwind, postcss configs.

**T-A028 (Tag UI)**: Created 4 tag components — TagBadge (colored inline badge), TagList (with delete), TagCreateDialog (modal with color picker), TagPicker (multi-select for task forms).

**T-A029 (Search/Filter/Sort)**: Created SearchInput (debounced 300ms), FilterBar (status, priority, tag, overdue), SortControls (4 fields + direction), Pagination.

**T-A030 (Task Form)**: Full task creation form with due date picker, reminder picker (disabled without due date), recurrence config (pattern, interval, end date), tag picker integration.

**T-A031 (WebSocket)**: WsClient class with exponential backoff reconnect (1s→30s max). Dashboard integrates real-time updates + reminder toast notifications.

**T-G004 (OTel Tracing)**: Created tracing.py in all 6 services. Updated all main.py lifespans and requirements.txt files with OTel deps.

**T-G007 (OTel Collector)**: K8s Deployment, Service, ConfigMap. Reference config at monitoring/otel/. Added to kustomization.yaml.

**Grafana Dashboards**: Created kafka-overview, task-metrics, infrastructure dashboards.

## Outcome

- ✅ Impact: All 66/66 tasks now implemented — project at 100% task completion
- 🧪 Tests: N/A — greenfield frontend + config files
- 📁 Files: 50+ files created/modified
- 🔁 Next prompts: /sp.adr microservice-expansion, validation/testing
- 🧠 Reflection: Direct file writes are much faster than subagents for bulk file creation

## Evaluation notes (flywheel)

- Failure modes observed: Subagents consumed excessive tokens on codebase exploration before writing; internal tool errors on parallel writes
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Use direct writes for bulk file creation, reserve subagents for complex research
