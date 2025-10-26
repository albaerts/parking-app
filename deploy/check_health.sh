#!/usr/bin/env bash
# check_health.sh <URL> [max_attempts] [sleep_seconds]
set -euo pipefail

URL=${1:-http://127.0.0.1:8000/health}
MAX_ATTEMPTS=${2:-10}
SLEEP=${3:-2}

attempt=1
while [ $attempt -le $MAX_ATTEMPTS ]; do
  echo "Health check attempt ${attempt}/${MAX_ATTEMPTS} -> ${URL}"
  if curl -fsS --max-time 5 "$URL" >/dev/null 2>&1; then
    echo "OK: ${URL} responded"
    exit 0
  fi
  attempt=$((attempt+1))
  sleep $SLEEP
done

echo "Health check failed after ${MAX_ATTEMPTS} attempts" >&2
exit 1
