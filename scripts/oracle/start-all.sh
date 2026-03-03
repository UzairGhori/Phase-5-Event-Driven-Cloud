#!/usr/bin/env bash
# Start all services in dependency order
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  Starting All Services (Oracle Cloud)"
echo "============================================"
echo ""

# 1. PostgreSQL (must be first — other services depend on it)
echo "[1/9] Starting PostgreSQL..."
bash "$SCRIPT_DIR/run-postgres.sh"
echo ""

# 2. Task API (depends on postgres)
echo "[2/9] Starting Task API..."
bash "$SCRIPT_DIR/run-task-api.sh"
echo ""

# 3-6. Consumer services (independent, can start in any order)
echo "[3/9] Starting Chat API..."
bash "$SCRIPT_DIR/run-chat-api.sh"
echo ""

echo "[4/9] Starting Reminder service..."
bash "$SCRIPT_DIR/run-reminder.sh"
echo ""

echo "[5/9] Starting Recurring service..."
bash "$SCRIPT_DIR/run-recurring.sh"
echo ""

echo "[6/9] Starting Audit service..."
bash "$SCRIPT_DIR/run-audit.sh"
echo ""

echo "[7/9] Starting WS Sync service..."
bash "$SCRIPT_DIR/run-ws-sync.sh"
echo ""

# 8. Frontend (depends on task-api and chat-api being reachable)
echo "[8/9] Starting Frontend..."
bash "$SCRIPT_DIR/run-frontend.sh"
echo ""

# 9. Nginx (must be last — proxies to all services)
echo "[9/9] Starting Nginx..."
bash "$SCRIPT_DIR/run-nginx.sh"
echo ""

echo "============================================"
echo "  All services started!"
echo "============================================"
echo ""
echo "Run 'bash $SCRIPT_DIR/status.sh' to check status"
echo ""

# Quick health check
echo "Waiting 5s for services to initialize..."
sleep 5

PUBLIC_IP="${PUBLIC_IP:-localhost}"
if curl -sf "http://localhost:${NGINX_PORT:-80}/api/health" &>/dev/null; then
    echo "Health check PASSED: http://$PUBLIC_IP/api/health"
else
    echo "Health check: API not yet responding (may still be starting)"
fi

echo ""
echo "Access the app at: http://$PUBLIC_IP"
