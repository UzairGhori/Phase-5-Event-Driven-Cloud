---
id: 013
title: CI/CD GROUP F Unified Pipeline
stage: green
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 003-event-driven-cloud
branch: 003-event-driven-cloud
user: uzair
command: sp.implement
labels: ["cicd", "github-actions", "docker", "kubernetes", "group-f"]
links:
  spec: specs/003-event-driven-cloud/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - .github/workflows/deploy.yml
  - specs/003-event-driven-cloud/tasks.md
tests:
  - none
---

## Prompt

Execute GROUP F tasks (CI/CD).

Create:

.github/workflows/deploy.yml

Pipeline must:
- Run tests
- Build Docker images
- Push to container registry
- Deploy to Kubernetes
- Use secrets securely
- Deploy only on main branch

Support:
- Minikube (dev)
- AKS/GKE (prod)

Follow best practices.

## Response snapshot

Created `.github/workflows/deploy.yml` — a unified CI/CD pipeline with 4 stages across 8 jobs:

**Stage 1 — Test (all PRs + main pushes):**
- `lint-backend`: ruff + mypy on backend/ and services/
- `lint-frontend`: eslint + tsc --noEmit on frontend/
- `test-backend`: pytest with PostgreSQL service container, coverage
- `test-frontend`: vitest with coverage
- `docker-build-check`: matrix build of all 7 Dockerfiles (PR only)

**Stage 2+3 — Build & Push (main only, after tests pass):**
- `build-and-push`: matrix job builds 7 Docker images, pushes to ghcr.io tagged with SHA
- Uses Docker Buildx with GHA cache for fast rebuilds
- GITHUB_TOKEN for registry auth (no external secrets needed)

**Stage 4 — Deploy (main only, after build):**
- `deploy-staging`: auto-deploy using kustomize edit set image + kubectl apply
- `deploy-production`: manual approval gate via GitHub Environments
- Multi-target support via `DEPLOY_TARGET` variable: aks (default), gke, minikube
- AKS: kubeconfig secret, GKE: service account + get-gke-credentials, Minikube: setup-minikube action

Key best practices:
- Concurrency control (cancel in-flight runs for same branch)
- Least-privilege permissions (contents: read, packages: write)
- Secrets via GitHub Environments (staging/production)
- No hardcoded credentials
- Rollout verification with 120s timeout
- fail-fast: false on matrix builds
- Coverage artifacts uploaded

Existing `ci.yaml` and `cd.yaml` preserved (plan §6.2 originals).

Marked T-F001 and T-F002 as done in tasks.md.

## Outcome

- ✅ Impact: Complete CI/CD pipeline for all 7 microservices with multi-cloud deploy support
- 🧪 Tests: No automated tests (workflow definition)
- 📁 Files: 1 created (.github/workflows/deploy.yml), 1 updated (tasks.md)
- 🔁 Next prompts: GROUP G (Monitoring & Logging)
- 🧠 Reflection: Unified pipeline cleaner than separate ci+cd; conditional steps handle PR vs main divergence

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Validate YAML syntax with actionlint
