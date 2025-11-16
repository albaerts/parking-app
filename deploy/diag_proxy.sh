#!/usr/bin/env bash
set -euo pipefail

# Quick diagnostics for proxy/frontend/backend on the server.
# Run on the server in the repo root: ./deploy/diag_proxy.sh

DC="docker compose"
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
fi

echo "== docker ps (names, status, ports) =="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo "\n== compose services =="
$DC -f docker-compose.prod.yml ps || true

echo "\n== check ports 80/443 bound =="
ss -tulpen | grep -E ':80 |:443 ' || netstat -tulpen 2>/dev/null | grep -E ':80 |:443 ' || echo "ss/netstat not available"

echo "\n== proxy container logs (last 200) =="
if docker ps -q -f name=parking_proxy >/dev/null 2>&1; then
  docker logs --tail 200 parking_proxy || true
else
  echo "parking_proxy not running"
fi

echo "\n== backend health via container network =="
if docker ps -q -f name=parking_backend >/dev/null 2>&1; then
  docker exec parking_backend wget -q -O - http://localhost:8000/health || echo "backend health endpoint unreachable"
else
  echo "parking_backend not running"
fi

CERT_DIR=/etc/letsencrypt/live/parking.gashis.ch
echo "\n== check TLS cert files on host =="
if [ -r "$CERT_DIR/fullchain.pem" ] && [ -r "$CERT_DIR/privkey.pem" ]; then
  echo "certs present: $CERT_DIR/fullchain.pem and privkey.pem"
  ls -l "$CERT_DIR"/*.pem
else
  echo "certs missing or not readable at $CERT_DIR"
fi

echo "\n== nginx config test inside image =="
if docker image inspect nginx:stable-alpine >/dev/null 2>&1; then
  TMPDIR=$(mktemp -d)
  cp deploy/nginx.conf "$TMPDIR/default.conf"
  echo "Testing nginx config syntax using stock image..."
  docker run --rm -v "$TMPDIR/default.conf:/etc/nginx/conf.d/default.conf:ro" nginx:stable-alpine nginx -t || true
  rm -rf "$TMPDIR"
else
  echo "nginx image not present; skipping config test"
fi

echo "\nDone. Review findings above."
