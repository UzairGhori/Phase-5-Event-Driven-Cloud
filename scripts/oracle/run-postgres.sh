#!/usr/bin/env bash
# Run PostgreSQL container
source "$(dirname "$0")/env.sh"

ensure_network
remove_container "$POSTGRES_CONTAINER"

echo "Starting PostgreSQL..."
docker run -d \
    --name "$POSTGRES_CONTAINER" \
    --network "$NETWORK_NAME" \
    --restart unless-stopped \
    -p "${POSTGRES_PORT}:5432" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -v todo-postgres-data:/var/lib/postgresql/data \
    postgres:16-alpine

echo "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" &>/dev/null; then
        echo "PostgreSQL is ready."
        exit 0
    fi
    sleep 1
done

echo "ERROR: PostgreSQL failed to become ready within 30s"
exit 1
