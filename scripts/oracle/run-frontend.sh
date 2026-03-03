#!/usr/bin/env bash
# Build and run the Frontend service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$FRONTEND_IMAGE" "docker/frontend.Dockerfile"
remove_container "$FRONTEND_CONTAINER"

echo "Starting Frontend on port $FRONTEND_PORT..."
docker run -d \
    --name "$FRONTEND_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${FRONTEND_PORT}:3000" \
    -e NODE_ENV=production \
    -e BACKEND_URL="http://${TASK_API_CONTAINER}:8000" \
    -e CHAT_API_URL="http://${CHAT_API_CONTAINER}:8001" \
    "$FRONTEND_IMAGE"

echo "Frontend started: $FRONTEND_CONTAINER"
