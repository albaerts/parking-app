#!/usr/bin/env bash
set -euo pipefail

# Projektwurzel relativ zu diesem Skript ermitteln
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# All-in-one Deploy für Debian 12 VPS mit Root-Login

# ===== Konfiguration =====
SERVER="s2591.rootserver.io"   # vom Nutzer geliefert (IP: 185.66.109.45)
SSH_USER="root"            # vom Nutzer bestätigt
REMOTE_DIR="/var/www/parking"
DOMAIN_API="api.gashis.ch"
DOMAIN_FE="parking.gashis.ch"

if [[ "$SERVER" == "your.server.tld" ]]; then
  echo "Bitte SERVER in deploy/deploy_all.sh setzen (Hostname oder IP)." >&2
  exit 1
fi

echo "[0/9] Vorab-Check: lokales Backend .env"
if [[ ! -f "$REPO_DIR/backend/.env" ]]; then
  echo "backend/.env fehlt. Lege es an (siehe backend/.env.example) und starte erneut." >&2
  exit 1
fi

echo "[1/9] Server-Grundsetup (Debian 12) via SSH"
ssh "$SSH_USER@$SERVER" bash -s << 'EOSSH'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt update
apt -y upgrade
apt -y install nginx certbot python3-certbot-nginx python3-venv python3-pip git curl rsync
# Falls Apache Port 80 blockiert, stoppen/deaktivieren
systemctl stop apache2 2>/dev/null || true
systemctl disable apache2 2>/dev/null || true
systemctl stop httpd 2>/dev/null || true
systemctl disable httpd 2>/dev/null || true
# Nginx sicherstellen
systemctl enable nginx || true
systemctl restart nginx || true
mkdir -p /var/www/parking
EOSSH

echo "[2/9] Rsync Code → $SSH_USER@$SERVER:$REMOTE_DIR"
rsync -az --delete \
  --exclude '.venv*' --exclude 'node_modules' --exclude '.git' \
  "$REPO_DIR/" "$SSH_USER@$SERVER:$REMOTE_DIR/"

echo "[3/9] Backend venv + requirements installieren"
ssh "$SSH_USER@$SERVER" bash -s << 'EOSSH'
set -euo pipefail
cd /var/www/parking
python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
EOSSH

echo "[4/9] systemd-Service anlegen/restarten"
ssh "$SSH_USER@$SERVER" bash -s << 'EOSSH'
set -euo pipefail
cat >/etc/systemd/system/parking-backend.service <<'EOF'
[Unit]
Description=Parking FastAPI backend (Uvicorn)
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/parking
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/var/www/parking/backend/.env
ExecStart=/var/www/parking/.venv/bin/python -m uvicorn backend.server:app --host 127.0.0.1 --port 8001 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable parking-backend
systemctl restart parking-backend
sleep 1
systemctl --no-pager status parking-backend || true
EOSSH

echo "[5/9] Nginx für API ($DOMAIN_API) konfigurieren"
ssh "$SSH_USER@$SERVER" bash -s << EOSSH
set -euo pipefail
cat >/etc/nginx/sites-available/$DOMAIN_API <<'EOF'
server {
    listen 80;
    server_name DOMAIN_API_PLACEHOLDER;

    location / {
        proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
sed -i "s/DOMAIN_API_PLACEHOLDER/$DOMAIN_API/g" /etc/nginx/sites-available/$DOMAIN_API
ln -sf /etc/nginx/sites-available/$DOMAIN_API /etc/nginx/sites-enabled/$DOMAIN_API
nginx -t
systemctl reload nginx
EOSSH

echo "[6/9] TLS für API einrichten (Certbot)"
ssh "$SSH_USER@$SERVER" bash -s << EOSSH
set -euo pipefail
if ! test -e /etc/letsencrypt/live/$DOMAIN_API/fullchain.pem; then
  certbot --nginx -d $DOMAIN_API --redirect -m admin@${HOSTNAME} --agree-tos -n || true
fi
nginx -t
systemctl reload nginx
EOSSH

echo "[7/9] Frontend-Build hochladen"
if [[ ! -d "$REPO_DIR/frontend/build" ]]; then
  echo "Fehlender Build-Ordner frontend/build. Bitte: (cd frontend && yarn build)" >&2
  exit 1
fi
rsync -az --delete "$REPO_DIR/frontend/build/" "$SSH_USER@$SERVER:$REMOTE_DIR/frontend_build/"

echo "[8/9] Nginx für FE ($DOMAIN_FE) konfigurieren"
ssh "$SSH_USER@$SERVER" bash -s << EOSSH
set -euo pipefail
cat >/etc/nginx/sites-available/$DOMAIN_FE <<'EOF'
server {
    listen 80;
    server_name DOMAIN_FE_PLACEHOLDER;

    location = / {
        return 302 /parking/;
    }

    location /parking/ {
        alias /var/www/parking/frontend_build/;
        index index.html;
    try_files \$uri \$uri/ /parking/index.html;
    }
}
EOF
sed -i "s/DOMAIN_FE_PLACEHOLDER/$DOMAIN_FE/g" /etc/nginx/sites-available/$DOMAIN_FE
ln -sf /etc/nginx/sites-available/$DOMAIN_FE /etc/nginx/sites-enabled/$DOMAIN_FE
nginx -t
systemctl reload nginx
EOSSH

echo "[9/9] TLS für FE einrichten (Certbot)"
ssh "$SSH_USER@$SERVER" bash -s << EOSSH
set -euo pipefail
if ! test -e /etc/letsencrypt/live/$DOMAIN_FE/fullchain.pem; then
  certbot --nginx -d $DOMAIN_FE --redirect -m admin@${HOSTNAME} --agree-tos -n || true
fi
nginx -t
systemctl reload nginx
EOSSH

echo "Fertig. Prüfe jetzt:"
echo "  - https://$DOMAIN_API/api/health"
echo "  - https://$DOMAIN_FE/parking/"
