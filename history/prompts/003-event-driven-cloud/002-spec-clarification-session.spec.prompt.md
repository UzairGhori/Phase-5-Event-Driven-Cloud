---
id: 002
title: Phase V Specification Clarification Session
stage: spec
date: 2026-02-22
surface: agent
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: main
user: architext
command: /sp.clarify
labels: ["clarification", "spec", "phase-v", "recurring-tasks", "aks", "ssr-proxy", "dapr-jobs"]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-event-driven-cloud/spec.md
  - CLAUDE.md
tests:
  - n/a (clarification phase)
---

## Prompt

/sp.clarify

## Response snapshot

Conducted a structured clarification session identifying 14 ambiguities in the Phase V spec. Presented 12 questions across 3 rounds of interactive clarification. All decisions resolved.

### Decisions Made (12 total)

| # | Topic | Decision | Impact |
|---|-------|----------|--------|
| 1 | Recurring task trigger | **Completion-based** (not cron). Next instance on `task.completed` event. | Removes `todo.recurring.due` topic; removes Dapr Jobs for recurrence; simplifies Recurring Task Service |
| 2 | Production K8s provider | **AKS (Azure)** | Azure Key Vault for secrets; AKS-specific manifests; Dapr native Azure support |
| 3 | Frontend → Backend path | **SSR Proxy** — Browser → Next.js Server → Dapr sidecar → Task API | Major architecture change from Phase II/III; browser never calls FastAPI directly |
| 4 | Local database (Minikube) | **Local PostgreSQL container** | Fully offline dev; Neon only in production |
| 5 | `is_overdue` computation | **Query-time computed** | Removed stored boolean column; computed as `due_date < now() AND status != completed` |
| 6 | Reminders per task | **Single reminder** (one `reminder_at` field) | No separate Reminder entity needed |
| 7 | Tag updates | **Add PATCH endpoint** | New `PATCH /api/tags/{tag_id}` for rename and recolor |
| 8 | Tag limits | **50/user, 10/task** | Added FR-048 for validation |
| 9 | Audit log writer | **Task API self-consumes** | No dedicated Audit Service; Task API subscribes to `todo.audit.log` |
| 10 | Reminder implementation | **Dapr Jobs API** | One-time scheduled job at `reminder_at` time |
| 11 | Search configuration | **`english` with stemming** | PostgreSQL tsvector `english` config for intelligent matching |
| 12 | Chatbot updates | **Yes, extend MCP tools** | Full feature parity: due_date, tags, reminders, search, filter in chatbot |

### Spec Changes Applied
- Added Clarifications section (12 Q&A entries)
- Changed `recurrence_cron` → `recurrence_interval` field
- Removed `todo.recurring.due` Kafka topic
- Removed `recurring.due` event schema
- Updated `is_overdue` from stored boolean to query-time computed
- Updated Dapr Jobs section to "Reminders Only"
- Added `PATCH /api/tags/{tag_id}` endpoint
- Updated all "AKS/GKE/OKE" references to "AKS (Azure)"
- Added FR-047 through FR-051 (chatbot, tag limits, tag update, SSR proxy, local PG)
- Added D-051 through D-053 (chatbot MCP updates)
- Renumbered backward compatibility deliverables to D-054 through D-056
- Updated service decomposition table
- Updated domain events table
- Updated CLAUDE.md with Key Architectural Decisions section

## Outcome

- Impact: All 14 ambiguities resolved. Spec is now internally consistent and ready for `/sp.plan`.
- Tests: n/a (clarification phase)
- Files: 2 files updated (spec.md, CLAUDE.md)
- Next prompts: `/sp.plan` to generate the architectural implementation plan
- Reflection: The SSR proxy decision and completion-based recurrence are the two most impactful architectural changes. Both simplify the system but require careful planning for the frontend migration.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review required
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Run `/sp.plan` to design implementation architecture based on clarified spec
