#!/usr/bin/env bash
set -euo pipefail
# Start FastAPI backend on 0.0.0.0:8000
# Usage: ./start.sh [--reload]
cd "$(dirname "$0")"
RELOAD=""
if [[ "${1:-}" == "--reload" ]]; then
  RELOAD="--reload"
fi
# Default to uvicorn if installed via pip from requirements.txt
exec uvicorn backend.server:app --host 0.0.0.0 --port 8000 $RELOAD
