#!/usr/bin/env bash
# Build and run the Task API service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$TASK_API_IMAGE" "docker/task-api.Dockerfile"
remove_container "$TASK_API_CONTAINER"

echo "Starting Task API on port $TASK_API_PORT..."
docker run -d \
    --name "$TASK_API_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${TASK_API_PORT}:8000" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    -e CORS_ORIGINS='["http://localhost:3000","http://localhost"]' \
    "$TASK_API_IMAGE"

echo "Task API started: $TASK_API_CONTAINER"
