#!/usr/bin/env bash
set -euo pipefail
BASE_LOCAL=${1:-http://localhost:8000}
BASE_DOMAIN=${2:-https://api.gashis.ch}

echo "Checking local health at $BASE_LOCAL..."
code_local_root=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_LOCAL/health" || true)
code_local_api=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_LOCAL/api/health" || true)
echo "  /health     => $code_local_root"
echo "  /api/health => $code_local_api"

echo "Checking domain health at $BASE_DOMAIN..."
code_domain_root=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_DOMAIN/health" || true)
code_domain_api=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_DOMAIN/api/health" || true)
echo "  /health     => $code_domain_root"
echo "  /api/health => $code_domain_api"
