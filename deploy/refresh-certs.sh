#!/usr/bin/env bash
set -euo pipefail

# Simple helper to sync Let's Encrypt certs from host into the repo deploy/certs directory
# Usage (on server as root or with sudo): ./deploy/refresh-certs.sh

SRC_DIR=/etc/letsencrypt
DEST_DIR=$(dirname "$0")/certs

echo "Syncing certs from ${SRC_DIR} to ${DEST_DIR} (read-only in container)..."
mkdir -p "${DEST_DIR}"
rsync -av --delete "${SRC_DIR}/" "${DEST_DIR}/"
chmod -R 440 "${DEST_DIR}"
echo "Certs synced. Ensure deploy user can read the files if needed."
