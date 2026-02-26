#!/usr/bin/env bash
# Task: T-D009 — Minikube full setup script
# Spec: SC-020 (deploy in under 5 minutes)
# Plan: §5.1
# Usage: bash scripts/setup-minikube.sh

set -euo pipefail

echo "=== Phase V: Todo App — Minikube Setup ==="

# 1. Start Minikube
echo "[1/8] Starting Minikube..."
minikube start --cpus=4 --memory=8192 --driver=docker --addons=ingress

# 2. Install Dapr
echo "[2/8] Installing Dapr on Kubernetes..."
dapr init -k --wait

# 3. Install Strimzi Operator
echo "[3/8] Installing Strimzi Kafka Operator..."
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "https://strimzi.io/install/latest?namespace=kafka" -n kafka
echo "Waiting for Strimzi operator to be ready..."
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator -n kafka --timeout=120s

# 4. Build Docker images inside Minikube
echo "[4/8] Building Docker images..."
eval $(minikube docker-env)

docker build -f docker/task-api.Dockerfile -t todo-app/task-api:latest .
docker build -f docker/chat-api.Dockerfile -t todo-app/chat-api:latest .
docker build -f docker/reminder-service.Dockerfile -t todo-app/reminder-service:latest .
docker build -f docker/recurring-service.Dockerfile -t todo-app/recurring-service:latest .
docker build -f docker/audit-service.Dockerfile -t todo-app/audit-service:latest .
docker build -f docker/ws-sync-service.Dockerfile -t todo-app/ws-sync-service:latest .
# docker build -f docker/frontend.Dockerfile -t todo-app/frontend:latest .  # Uncomment when frontend is ready

# 5. Apply namespaces and secrets
echo "[5/8] Applying namespaces and secrets..."
kubectl apply -f k8s/local/namespaces/
kubectl apply -f k8s/local/secrets/

# 6. Deploy infrastructure
echo "[6/8] Deploying PostgreSQL and Kafka..."
kubectl apply -f k8s/local/infrastructure/postgresql/
kubectl apply -f k8s/local/infrastructure/strimzi/

echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=Ready pod -l app=postgresql -n todo-app --timeout=120s

echo "Waiting for Kafka cluster to be ready..."
kubectl wait kafka/todo-kafka --for=condition=Ready -n kafka --timeout=300s || echo "Kafka may still be starting..."

# 7. Deploy Dapr components and services
echo "[7/8] Deploying Dapr components and application services..."
kubectl apply -f dapr/components/pubsub-kafka-local.yaml
kubectl apply -f dapr/components/statestore-postgresql.yaml
kubectl apply -f dapr/components/secrets-kubernetes.yaml
kubectl apply -f dapr/components/subscriptions.yaml
kubectl apply -f k8s/local/services/

# 8. Deploy networking
echo "[8/8] Deploying ingress..."
kubectl apply -f k8s/local/networking/

# Wait for all pods
echo ""
echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=Ready pod --all -n todo-app --timeout=180s || true

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services:"
kubectl get pods -n todo-app
echo ""
echo "Access the app:"
echo "  minikube tunnel  (in a separate terminal)"
echo "  Then visit: http://localhost"
echo ""
echo "Or use port-forward:"
echo "  bash scripts/port-forward.sh"
