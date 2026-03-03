#!/usr/bin/env bash
# Build and run the Audit service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$AUDIT_IMAGE" "docker/audit-service.Dockerfile"
remove_container "$AUDIT_CONTAINER"

echo "Starting Audit service on port $AUDIT_PORT..."
docker run -d \
    --name "$AUDIT_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${AUDIT_PORT}:8004" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    "$AUDIT_IMAGE"

echo "Audit service started: $AUDIT_CONTAINER"
