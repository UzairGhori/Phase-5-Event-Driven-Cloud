#!/usr/bin/env bash
# Build and run the Recurring service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$RECURRING_IMAGE" "docker/recurring-service.Dockerfile"
remove_container "$RECURRING_CONTAINER"

echo "Starting Recurring service on port $RECURRING_PORT..."
docker run -d \
    --name "$RECURRING_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${RECURRING_PORT}:8003" \
    -e SECRET_KEY="$SECRET_KEY" \
    "$RECURRING_IMAGE"

echo "Recurring service started: $RECURRING_CONTAINER"
