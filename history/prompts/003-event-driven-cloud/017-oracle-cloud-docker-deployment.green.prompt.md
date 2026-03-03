---
id: 017
title: Oracle Cloud Free Tier Docker Deployment
stage: green
date: 2026-03-03
surface: agent
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: main
user: uzair
command: implement oracle deployment plan
labels: ["oracle-cloud", "docker", "deployment", "arm64", "free-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - nginx/nginx.conf
  - scripts/oracle/env.sh
  - scripts/oracle/run-postgres.sh
  - scripts/oracle/run-task-api.sh
  - scripts/oracle/run-chat-api.sh
  - scripts/oracle/run-reminder.sh
  - scripts/oracle/run-recurring.sh
  - scripts/oracle/run-audit.sh
  - scripts/oracle/run-ws-sync.sh
  - scripts/oracle/run-frontend.sh
  - scripts/oracle/run-nginx.sh
  - scripts/oracle/start-all.sh
  - scripts/oracle/stop-all.sh
  - scripts/oracle/status.sh
  - scripts/deploy-oracle.sh
  - DEPLOYMENT.md
tests:
  - Manual: docker container startup and health check verification
---

## Prompt

Implement the Oracle Cloud Free Tier deployment plan using individual run scripts (not docker-compose). Create nginx reverse proxy config, per-service Docker run scripts, orchestrator scripts, remote deployment script, and update DEPLOYMENT.md.

## Response snapshot

Created 16 files for Oracle Cloud Free Tier deployment:
- `nginx/nginx.conf` — Reverse proxy routing (/ws→ws-sync, /api/chat→chat-api, /api→task-api, /→frontend)
- `scripts/oracle/env.sh` — Shared env vars, container names, helper functions (ensure_network, build_image, remove_container)
- 9 individual run scripts (`run-postgres.sh` through `run-nginx.sh`) — Each builds and runs one Docker container on a shared bridge network
- `scripts/oracle/start-all.sh` — Orchestrates all 9 services in dependency order with health check
- `scripts/oracle/stop-all.sh` — Tears down all containers (optional network/volume removal)
- `scripts/oracle/status.sh` — Shows container status and runs health checks
- `scripts/deploy-oracle.sh` — 8-phase remote deployment (SSH validate → Docker install → upload → env config → build/deploy → firewall → health check → output URL)
- Updated `DEPLOYMENT.md` with "Option 5: Oracle Cloud Free Tier" section

## Outcome

- ✅ Impact: Full deployment pipeline for free-tier cloud hosting on ARM64 VM
- 🧪 Tests: Manual verification via status.sh and health endpoints
- 📁 Files: 16 files created/modified
- 🔁 Next prompts: Test deployment on actual OCI VM, add HTTPS/TLS with Let's Encrypt
- 🧠 Reflection: Individual run scripts give more granular control than docker-compose; shared env.sh avoids duplication

## Evaluation notes (flywheel)

- Failure modes observed: None — clean implementation
- Graders run and results (PASS/FAIL): N/A (infrastructure scripts, not unit-testable)
- Prompt variant (if applicable): User redirected from docker-compose to individual scripts mid-implementation
- Next experiment: Add Let's Encrypt TLS automation to deploy-oracle.sh
