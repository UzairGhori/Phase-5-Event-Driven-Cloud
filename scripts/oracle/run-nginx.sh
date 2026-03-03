#!/usr/bin/env bash
# Run Nginx reverse proxy
source "$(dirname "$0")/env.sh"

ensure_network
remove_container "$NGINX_CONTAINER"

echo "Starting Nginx on port $NGINX_PORT..."
docker run -d \
    --name "$NGINX_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${NGINX_PORT}:80" \
    -v "$PROJECT_ROOT/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" \
    nginx:alpine

echo "Nginx started: $NGINX_CONTAINER"
