#!/usr/bin/env bash
# Quick-Setup für einen Ubuntu-Server
# Ziel: api.gashis.ch -> Nginx (TLS) -> Uvicorn (FastAPI auf 127.0.0.1:8000)
#
# Voraussetzungen:
# - Du hast das Projekt nach /opt/parking-app kopiert (z.B. via scp/rsync)
# - DNS A-Record: api.gashis.ch -> öffentliche IP dieses Servers
# - OS: Ubuntu 20.04/22.04/24.04 (root)
#
# Nutzung:
#   sudo bash scripts/setup_server_ubuntu.sh api.gashis.ch /opt/parking-app you@example.com
set -euo pipefail
DOMAIN=${1:-api.gashis.ch}
APP_DIR=${2:-/opt/parking-app}
EMAIL=${3:-you@example.com}

if [[ $EUID -ne 0 ]]; then
  echo "Bitte als root ausführen (sudo)." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx python3-venv python3-pip curl

# Firewall (optional)
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
fi

# Nginx vHost platzieren
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
cp "${APP_DIR}/infra/nginx/api.gashis.ch.conf" \
   "/etc/nginx/sites-available/${DOMAIN}.conf"
# Symlink aktivieren
ln -sf "/etc/nginx/sites-available/${DOMAIN}.conf" \
       "/etc/nginx/sites-enabled/${DOMAIN}.conf"
nginx -t
systemctl reload nginx

# TLS-Zertifikat via Certbot holen (auto-redirect aktivieren)
certbot --nginx -d "${DOMAIN}" --agree-tos -m "${EMAIL}" --redirect -n || true

# Python venv + Dependencies
mkdir -p "${APP_DIR}"
cd "${APP_DIR}/backend"
python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/pip" install --upgrade pip wheel setuptools
"${APP_DIR}/.venv/bin/pip" install -r requirements.txt

# systemd Service installieren (Pfad in Service anpassen)
cp "${APP_DIR}/backend/uvicorn.service" /etc/systemd/system/uvicorn.service
sed -i "s|/opt/parking-app/backend|${APP_DIR}/backend|g" /etc/systemd/system/uvicorn.service
# Optional: venv in PATH setzen
sed -i "s|^# Environment=\"PATH=.*|Environment=\"PATH=${APP_DIR}/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"|" /etc/systemd/system/uvicorn.service

systemctl daemon-reload
systemctl enable --now uvicorn
sleep 2
systemctl --no-pager --full status uvicorn || true

# Sanity Checks
set +e
curl -sS -o /dev/null -w "local /health %\{http_code\}\n" http://127.0.0.1:8000/health
curl -sS -o /dev/null -w "local /api/health %\{http_code\}\n" http://127.0.0.1:8000/api/health
curl -sS -o /dev/null -w "domain /health %\{http_code\}\n" https://${DOMAIN}/health
curl -sS -o /dev/null -w "domain /api/health %\{http_code\}\n" https://${DOMAIN}/api/health
set -e

echo "Fertig. Wenn domain /api/health nicht 200 ist, prüfe DNS, Nginx und den uvicorn-Service."