#!/usr/bin/env bash
# Task: T-D009 — Port-forward script for local development
set -euo pipefail

echo "=== Phase V: Port Forwarding ==="
echo "Starting port-forwards (Ctrl+C to stop all)..."
echo ""
echo "  Task API:    http://localhost:8000"
echo "  Chat API:    http://localhost:8001"
echo "  Frontend:    http://localhost:3000"
echo "  PostgreSQL:  localhost:5432"
echo ""

# Run all port-forwards in background
kubectl port-forward svc/task-api 8000:8000 -n todo-app &
kubectl port-forward svc/chat-api 8001:8001 -n todo-app &
kubectl port-forward svc/frontend 3000:3000 -n todo-app &
kubectl port-forward svc/postgresql 5432:5432 -n todo-app &

# Wait for any to exit
wait
