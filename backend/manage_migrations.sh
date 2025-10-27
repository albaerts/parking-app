#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic CLI not found. Trying python -m alembic..."
  python3 -m alembic -c "$HERE/alembic.ini" upgrade head
else
  alembic -c "$HERE/alembic.ini" upgrade head
fi

echo "Alembic migrations applied."
