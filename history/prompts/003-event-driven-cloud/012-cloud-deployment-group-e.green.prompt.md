---
id: 012
title: Cloud Deployment GROUP E Implementation
stage: green
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: uzair
command: implement
labels: ["cloud-deployment", "aks", "kubernetes", "production", "group-e"]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - k8s/production/services/task-api.yaml
  - k8s/production/services/chat-api.yaml
  - k8s/production/services/reminder-service.yaml
  - k8s/production/services/recurring-service.yaml
  - k8s/production/services/audit-service.yaml
  - k8s/production/services/ws-sync-service.yaml
  - k8s/production/services/frontend.yaml
  - scripts/deploy-aks.sh
  - specs/003-event-driven-cloud/tasks.md
tests:
  - none
---

## Prompt

Implement the following plan:

# Plan: GROUP E — Cloud Deployment (AKS)

## Context

All GROUP E files (T-E001 through T-E007) already exist under `k8s/production/`. The primary work is:
1. Fix resource limit deviations — 6 of 7 service manifests have resource limits below plan §5.2 targets
2. Add missing Dapr annotations to frontend deployment
3. Create `scripts/deploy-aks.sh` — AKS provisioning + deployment script (does not exist yet)
4. Mark T-E001–T-E007 as done in tasks.md
5. Create PHR 012

## Response snapshot

Implemented GROUP E — Cloud Deployment (AKS) in full:

1. **Fixed resource limits** across all 7 production service YAMLs to match plan §5.2:
   - task-api: CPU request 200m → 250m
   - chat-api: all resources doubled (100m/250m/128Mi/256Mi → 250m/500m/256Mi/512Mi)
   - reminder, recurring, audit, ws-sync: all bumped from 50m/150m/64Mi/128Mi → 100m/250m/128Mi/256Mi
   - frontend: all resources doubled (100m/250m/128Mi/256Mi → 250m/500m/256Mi/512Mi)

2. **Added Dapr annotations** to frontend deployment (was missing sidecar config)

3. **Created `scripts/deploy-aks.sh`** — full 8-phase AKS deployment script:
   - Phase 1: Azure resource group
   - Phase 2: AKS cluster (Standard_D2s_v3, 3 nodes, managed identity)
   - Phase 3: Get credentials
   - Phase 4: Install Dapr v1.14.4
   - Phase 5: NGINX Ingress + cert-manager via Helm
   - Phase 6: Namespaces + K8s secrets (Neon/JWT/OpenAI/Redpanda)
   - Phase 7: Apply production manifests via kustomize
   - Phase 8: Wait for rollout, verify pods, print status

4. **Marked T-E001–T-E007 as done** in tasks.md

5. **Validated**: HPA, PDB, Ingress, Network Policies, and Kustomization already compliant — no changes needed

## Outcome

- ✅ Impact: All GROUP E tasks complete; production AKS manifests aligned with plan §5.2
- 🧪 Tests: No automated tests (infrastructure manifests)
- 📁 Files: 7 modified, 1 created, 1 tasks.md updated
- 🔁 Next prompts: GROUP F (CI/CD) or GROUP G (Monitoring)
- 🧠 Reflection: Audit-first approach ensured minimal, targeted changes; no unnecessary refactoring

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Validate with kubectl apply --dry-run=client
