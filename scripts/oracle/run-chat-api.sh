#!/usr/bin/env bash
# Build and run the Chat API service
source "$(dirname "$0")/env.sh"

ensure_network
build_image "$CHAT_API_IMAGE" "docker/chat-api.Dockerfile"
remove_container "$CHAT_API_CONTAINER"

echo "Starting Chat API on port $CHAT_API_PORT..."
docker run -d \
    --name "$CHAT_API_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${CHAT_API_PORT}:8001" \
    -e SECRET_KEY="$SECRET_KEY" \
    "$CHAT_API_IMAGE"

echo "Chat API started: $CHAT_API_CONTAINER"
