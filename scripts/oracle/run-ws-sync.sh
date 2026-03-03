#!/usr/bin/env bash
# Build and run the WebSocket Sync service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$WS_SYNC_IMAGE" "docker/ws-sync-service.Dockerfile"
remove_container "$WS_SYNC_CONTAINER"

echo "Starting WS Sync service on port $WS_SYNC_PORT..."
docker run -d \
    --name "$WS_SYNC_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${WS_SYNC_PORT}:8005" \
    -e SECRET_KEY="$SECRET_KEY" \
    "$WS_SYNC_IMAGE"

echo "WS Sync service started: $WS_SYNC_CONTAINER"
