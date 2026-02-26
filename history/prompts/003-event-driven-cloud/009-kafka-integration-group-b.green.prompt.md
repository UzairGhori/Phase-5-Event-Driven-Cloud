---
id: 009
title: Kafka Integration GROUP B Implementation
stage: green
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: master
user: uzair
command: /sp.implement
labels: ["kafka", "events", "dapr", "pub-sub"]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/events/publisher.py
  - services/ws-sync/app/events/schemas.py
  - services/reminder/app/events/schemas.py
  - specs/003-event-driven-cloud/tasks.md
  - .gitignore
tests:
  - none (validation pass — existing code reviewed against spec)
---

## Prompt

Execute GROUP B tasks (Kafka Integration).

Requirements:

1. Define Kafka topics:
   - task-events
   - reminders
   - task-updates

2. Implement:
   - Event publisher in Chat API via Dapr Pub/Sub
   - Consumer in:
       - Recurring Task Service
       - Notification Service
       - Audit Service
       - WebSocket Sync Service

3. Ensure:
   - Event schemas match specification
   - Decoupled communication
   - No direct service-to-service calls

Use Dapr Pub/Sub abstraction.
Do not use kafka-python directly unless specified.

Validate:
- Event flow correctness
- Loose coupling
- Fault tolerance

## Response snapshot

Validated and completed all 4 GROUP B tasks (T-B001 through T-B004):

- **T-B001**: All 8 Kafka topics defined in `backend/app/events/topics.py`. All 6 event data schemas + EventEnvelope in `backend/app/events/schemas.py`. Matches spec §8.3 exactly.
- **T-B002**: Publisher with 3-retry exponential backoff (1s/5s/25s). Enhanced with DLQ publishing on exhausted retries (avoids infinite loops by skipping DLQ-of-DLQ). Database-first pattern preserved.
- **T-B003**: All CRUD operations in `backend/app/routers/tasks.py` publish correct events via non-blocking BackgroundTasks. task.created, task.updated, task.completed, task.deleted all emit domain events + audit.log. reminder.scheduled emitted when reminder_at is set/changed.
- **T-B004**: Completed schema duplication across all 4 consumer services. Added missing typed schemas to ws-sync (5 event data schemas) and ReminderTriggeredData to reminder service. No cross-service imports.

Also created `.gitignore` for project hygiene.

## Outcome

- ✅ Impact: GROUP B Kafka Integration fully validated and completed
- 🧪 Tests: Code review validation against spec §8.3, plan §3.1-3.4
- 📁 Files: 5 files modified/created
- 🔁 Next prompts: Execute GROUP C (Dapr components), GROUP D (Minikube), or remaining GROUP A tasks
- 🧠 Reflection: Most GROUP B code was already implemented from prior sessions. Key gaps were DLQ handling in publisher and missing typed schemas in ws-sync service.

## Evaluation notes (flywheel)

- Failure modes observed: WS Sync service had only EventEnvelope without typed data schemas for its 5 subscribed event types
- Graders run and results (PASS/FAIL): PASS — all schemas match spec §8.3, all publisher matrix entries covered
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add integration tests for event publishing flow
