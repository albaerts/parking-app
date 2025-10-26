#!/usr/bin/env bash
# backup_db.sh [dest_dir]
set -euo pipefail
set -euo pipefail
#!/usr/bin/env bash
# backup_db.sh [dest_dir]
set -euo pipefail

DEST_DIR=${1:-$(dirname "$0")/backups}
SRC_DB=./backend/parking.db

if [ ! -f "$SRC_DB" ]; then
  echo "No database file found at $SRC_DB, skipping backup"
  exit 0
fi

mkdir -p "$DEST_DIR"
TS=$(date +"%F_%H%M%S")
DEST_FILE="$DEST_DIR/parking.db.$TS"

cp -v "$SRC_DB" "$DEST_FILE"
chmod 640 "$DEST_FILE"
echo "Backup written to $DEST_FILE"
