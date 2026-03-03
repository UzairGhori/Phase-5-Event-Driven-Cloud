#!/usr/bin/env bash
# Stop and remove all service containers
set -euo pipefail

source "$(dirname "$0")/env.sh"

CONTAINERS=(
    "$NGINX_CONTAINER"
    "$FRONTEND_CONTAINER"
    "$WS_SYNC_CONTAINER"
    "$AUDIT_CONTAINER"
    "$RECURRING_CONTAINER"
    "$REMINDER_CONTAINER"
    "$CHAT_API_CONTAINER"
    "$TASK_API_CONTAINER"
    "$POSTGRES_CONTAINER"
)

echo "============================================"
echo "  Stopping All Services"
echo "============================================"
echo ""

for container in "${CONTAINERS[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "Stopping $container..."
        docker stop "$container" 2>/dev/null || true
        docker rm "$container" 2>/dev/null || true
    else
        echo "Skipping $container (not found)"
    fi
done

echo ""

# Optionally remove network
if [ "${REMOVE_NETWORK:-false}" = "true" ]; then
    echo "Removing network: $NETWORK_NAME"
    docker network rm "$NETWORK_NAME" 2>/dev/null || true
fi

# Optionally remove volumes
if [ "${REMOVE_VOLUMES:-false}" = "true" ]; then
    echo "Removing volume: todo-postgres-data"
    docker volume rm todo-postgres-data 2>/dev/null || true
fi

echo ""
echo "All services stopped."
echo ""
echo "To also remove the network:  REMOVE_NETWORK=true bash $0"
echo "To also remove data volumes: REMOVE_VOLUMES=true bash $0"
