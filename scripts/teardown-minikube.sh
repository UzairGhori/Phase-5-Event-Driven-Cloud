#!/usr/bin/env bash
# Task: T-D009 — Minikube teardown script
set -euo pipefail

echo "=== Phase V: Todo App — Minikube Teardown ==="

echo "Deleting application resources..."
kubectl delete -f k8s/local/networking/ --ignore-not-found
kubectl delete -f k8s/local/services/ --ignore-not-found
kubectl delete -f dapr/components/ --ignore-not-found
kubectl delete -f k8s/local/infrastructure/strimzi/ --ignore-not-found
kubectl delete -f k8s/local/infrastructure/postgresql/ --ignore-not-found
kubectl delete -f k8s/local/secrets/ --ignore-not-found

echo "Uninstalling Dapr..."
dapr uninstall -k || true

echo "Deleting namespaces..."
kubectl delete namespace todo-app --ignore-not-found
kubectl delete namespace kafka --ignore-not-found
kubectl delete namespace monitoring --ignore-not-found

echo "Stopping Minikube..."
minikube stop

echo ""
echo "=== Teardown Complete ==="
echo "Run 'minikube delete' to fully remove the cluster."
