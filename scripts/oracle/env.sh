#!/usr/bin/env bash
# Shared environment variables for Oracle Cloud deployment
# Source this file in each run script: source "$(dirname "$0")/env.sh"

set -euo pipefail

# ── Docker network ──
NETWORK_NAME="todo-network"

# ── Container names ──
POSTGRES_CONTAINER="todo-postgres"
TASK_API_CONTAINER="todo-task-api"
CHAT_API_CONTAINER="todo-chat-api"
REMINDER_CONTAINER="todo-reminder"
RECURRING_CONTAINER="todo-recurring"
AUDIT_CONTAINER="todo-audit"
WS_SYNC_CONTAINER="todo-ws-sync"
FRONTEND_CONTAINER="todo-frontend"
NGINX_CONTAINER="todo-nginx"

# ── Image names ──
TASK_API_IMAGE="todo-task-api:latest"
CHAT_API_IMAGE="todo-chat-api:latest"
REMINDER_IMAGE="todo-reminder:latest"
RECURRING_IMAGE="todo-recurring:latest"
AUDIT_IMAGE="todo-audit:latest"
WS_SYNC_IMAGE="todo-ws-sync:latest"
FRONTEND_IMAGE="todo-frontend:latest"

# ── Ports ──
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
TASK_API_PORT="${TASK_API_PORT:-8000}"
CHAT_API_PORT="${CHAT_API_PORT:-8001}"
REMINDER_PORT="${REMINDER_PORT:-8002}"
RECURRING_PORT="${RECURRING_PORT:-8003}"
AUDIT_PORT="${AUDIT_PORT:-8004}"
WS_SYNC_PORT="${WS_SYNC_PORT:-8005}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
NGINX_PORT="${NGINX_PORT:-80}"

# ── Database ──
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-todo_app}"
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER}:5432/${POSTGRES_DB}"

# ── App secrets ──
SECRET_KEY="${SECRET_KEY:-change-me-in-production}"

# ── Project root (relative to this script) ──
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ── Helper: ensure network exists ──
ensure_network() {
    if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
        echo "Creating Docker network: $NETWORK_NAME"
        docker network create "$NETWORK_NAME"
    fi
}

# ── Helper: build image ──
build_image() {
    local image_name="$1"
    local dockerfile="$2"
    echo "Building $image_name from $dockerfile ..."
    docker build -t "$image_name" -f "$PROJECT_ROOT/$dockerfile" "$PROJECT_ROOT"
}

# ── Helper: stop & remove container if exists ──
remove_container() {
    local name="$1"
    if docker ps -a --format '{{.Names}}' | grep -q "^${name}$"; then
        echo "Removing existing container: $name"
        docker stop "$name" 2>/dev/null || true
        docker rm "$name" 2>/dev/null || true
    fi
}
