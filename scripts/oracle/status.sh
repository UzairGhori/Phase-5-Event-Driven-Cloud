#!/usr/bin/env bash
# Show status of all service containers
set -euo pipefail

source "$(dirname "$0")/env.sh"

CONTAINERS=(
    "$POSTGRES_CONTAINER"
    "$TASK_API_CONTAINER"
    "$CHAT_API_CONTAINER"
    "$REMINDER_CONTAINER"
    "$RECURRING_CONTAINER"
    "$AUDIT_CONTAINER"
    "$WS_SYNC_CONTAINER"
    "$FRONTEND_CONTAINER"
    "$NGINX_CONTAINER"
)

echo "============================================"
echo "  Service Status"
echo "============================================"
echo ""

printf "%-25s %-12s %-20s\n" "CONTAINER" "STATUS" "PORTS"
printf "%-25s %-12s %-20s\n" "---------" "------" "-----"

ALL_UP=true
for container in "${CONTAINERS[@]}"; do
    STATUS=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
    PORTS=$(docker port "$container" 2>/dev/null | head -1 || echo "-")
    printf "%-25s %-12s %-20s\n" "$container" "$STATUS" "$PORTS"
    if [ "$STATUS" != "running" ]; then
        ALL_UP=false
    fi
done

echo ""

# Health checks
echo "Health Checks:"
echo "--------------"

check_health() {
    local name="$1" url="$2"
    if curl -sf --max-time 3 "$url" &>/dev/null; then
        echo "  $name: OK"
    else
        echo "  $name: FAIL"
        ALL_UP=false
    fi
}

check_health "Nginx"    "http://localhost:${NGINX_PORT}/nginx-health"
check_health "Task API" "http://localhost:${NGINX_PORT}/api/health"
check_health "Frontend" "http://localhost:${NGINX_PORT}/"

echo ""
if [ "$ALL_UP" = true ]; then
    echo "All services are running."
else
    echo "WARNING: Some services are not healthy."
    echo "Check logs with: docker logs <container-name>"
fi
