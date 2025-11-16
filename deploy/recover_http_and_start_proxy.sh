#!/usr/bin/env bash
set -euo pipefail

# HTTP-Fallback aktivieren und Proxy starten

DC="docker-compose"
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DC="docker compose"
fi

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

REGISTRY=${REGISTRY:-ghcr.io}
REPO_OWNER=${REPO_OWNER:-albaerts}
IMAGE_TAG=${IMAGE_TAG:-latest}
export REGISTRY REPO_OWNER IMAGE_TAG

echo "[info] Verwende REGISTRY=$REGISTRY REPO_OWNER=$REPO_OWNER IMAGE_TAG=$IMAGE_TAG"

echo "[step] Schreibe docker-compose.override.yml für HTTP-only Fallback"
cat > docker-compose.override.yml <<'YAML'
version: "3.8"
services:
  proxy:
    ports:
      - "80:80"
    volumes:
      - ./deploy/nginx.http.conf:/etc/nginx/conf.d/default.conf:ro
YAML

echo "[step] Validierung: existiert deploy/nginx.http.conf?"
test -f deploy/nginx.http.conf || {
  echo "[error] deploy/nginx.http.conf fehlt. Bitte aus dem Repo übernehmen." >&2
  exit 1
}

echo "[step] Images ziehen (frontend/backend)"
if [ "$DC" = "docker-compose" ]; then
  $DC -f docker-compose.prod.yml pull frontend backend
else
  $DC -f docker-compose.prod.yml pull frontend backend
fi

echo "[step] Backend, Frontend und Proxy hochfahren (HTTP-only)"
if [ "$DC" = "docker-compose" ]; then
  $DC -f docker-compose.prod.yml up -d --force-recreate backend frontend proxy
else
  $DC -f docker-compose.prod.yml up -d --force-recreate backend frontend proxy
fi

echo "[step] Status"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo "[step] Lokaler Smoke-Test"
curl -sS -m 5 -w "HTTP:%{http_code}\n" http://localhost/ || true
curl -sS -m 5 -w "HTTP:%{http_code}\n" http://localhost/api/health || true

echo "[done] Wenn HTTP 200 zurückkommt, ist der Proxy wieder erreichbar. Danach TLS wieder aktivieren."
