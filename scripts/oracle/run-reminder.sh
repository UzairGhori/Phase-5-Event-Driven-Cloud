#!/usr/bin/env bash
# Build and run the Reminder service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$REMINDER_IMAGE" "docker/reminder-service.Dockerfile"
remove_container "$REMINDER_CONTAINER"

echo "Starting Reminder service on port $REMINDER_PORT..."
docker run -d \
    --name "$REMINDER_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${REMINDER_PORT}:8002" \
    -e SECRET_KEY="$SECRET_KEY" \
    "$REMINDER_IMAGE"

echo "Reminder service started: $REMINDER_CONTAINER"
