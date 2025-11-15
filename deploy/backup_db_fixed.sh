#!/usr/bin/env bash
set -euo pipefail

# Usage: ./deploy/backup_db_fixed.sh [TARGET_DIR]
# Creates a timestamped pg_dump (gzip) from the running postgres container.
# Requires a running container named "parking_postgres".

TARGET_DIR=${1:-./deploy/backups}
mkdir -p "$TARGET_DIR"

TS=$(date +%Y%m%d-%H%M%S)
USER=${POSTGRES_USER:-parking}
DB=${POSTGRES_DB:-parkingdb}
CONTAINER=${POSTGRES_CONTAINER_NAME:-parking_postgres}

OUT_FILE="$TARGET_DIR/${DB}_${TS}.sql.gz"

echo "Creating Postgres backup: $OUT_FILE"
if docker ps -q -f name=$CONTAINER >/dev/null 2>&1; then
  docker exec -i "$CONTAINER" pg_dump -U "$USER" -d "$DB" | gzip > "$OUT_FILE"
  echo "Backup complete: $OUT_FILE"
else
  echo "Error: container $CONTAINER not running" >&2
  exit 1
fi
