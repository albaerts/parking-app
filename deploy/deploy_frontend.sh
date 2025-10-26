#!/usr/bin/env bash
set -euo pipefail

# Projektwurzel relativ zu diesem Skript ermitteln
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ===== Konfiguration anpassen =====
SERVER="s2591.rootserver.io"
SSH_USER="root"
REMOTE_DIR="/var/www/parking"
DOMAIN_FE="parking.gashis.ch"

if [[ "$SERVER" == "your.server.tld" ]]; then
  echo "Bitte SERVER in deploy_frontend.sh setzen." >&2
  exit 1
fi

BUILD_DIR="$REPO_DIR/frontend/build"
if [[ ! -d "$BUILD_DIR" ]]; then
  echo "Build-Ordner $BUILD_DIR fehlt. Bitte im Ordner frontend: yarn install && yarn build ausführen." >&2
  exit 1
fi

echo "[1/5] Upload build → $SSH_USER@$SERVER:$REMOTE_DIR/frontend_build/"
rsync -az --delete "$BUILD_DIR/" "$SSH_USER@$SERVER:$REMOTE_DIR/frontend_build/"

ssh "$SSH_USER@$SERVER" bash -s << 'EOSSH'
set -euo pipefail
REMOTE_DIR="/var/www/parking"

echo "[2/5] Nginx-Site für parking.gashis.ch"
sudo tee /etc/nginx/sites-available/parking.gashis.ch >/dev/null <<'EOF'
server {
    listen 80;
    server_name parking.gashis.ch;

    # Optional: redirect root to /parking/
    location = / {
        return 302 /parking/;
    }

    # Serve CRA build under /parking/
    location /parking/ {
        alias /var/www/parking/frontend_build/;
        index index.html;
        try_files $uri $uri/ /parking/index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/parking.gashis.ch /etc/nginx/sites-enabled/parking.gashis.ch
sudo nginx -t
sudo systemctl reload nginx

echo "[3/5] Certbot TLS für parking.gashis.ch (falls noch nicht vorhanden)"
if ! sudo test -e /etc/letsencrypt/live/parking.gashis.ch/fullchain.pem; then
  sudo certbot --nginx -d parking.gashis.ch --redirect -m admin@${HOSTNAME} --agree-tos -n || true
fi

echo "[4/5] Nginx reload nach Zertifikat"
sudo nginx -t
sudo systemctl reload nginx

echo "[5/5] Done → https://parking.gashis.ch/parking/"
EOSSH
