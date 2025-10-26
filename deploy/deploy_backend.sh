#!/usr/bin/env bash
set -euo pipefail

# Projektwurzel relativ zu diesem Skript ermitteln
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ===== Konfiguration anpassen =====
SERVER="s2591.rootserver.io"
SSH_USER="root"
REMOTE_DIR="/var/www/parking"
DOMAIN_API="api.gashis.ch"

# ===== Checks =====
if [[ "$SERVER" == "your.server.tld" ]]; then
  echo "Bitte SERVER in deploy_backend.sh setzen." >&2
  exit 1
fi

# ===== Code hochladen =====
echo "[1/6] Rsync Code → $SSH_USER@$SERVER:$REMOTE_DIR"
rsync -az --delete \
  --exclude '.venv*' --exclude 'node_modules' --exclude '.git' \
  "$REPO_DIR/" "$SSH_USER@$SERVER:$REMOTE_DIR/"

# ===== Remote Befehle =====
ssh "$SSH_USER@$SERVER" bash -s << 'EOSSH'
set -euo pipefail
REMOTE_DIR="/var/www/parking"
cd "$REMOTE_DIR"

echo "[2/6] Python venv + requirements"
python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "[3/6] .env prüfen"
if [[ ! -f backend/.env ]]; then
  echo "Fehlende backend/.env! Bitte anlegen und erneut ausführen." >&2
  exit 1
fi

echo "[4/6] systemd-Unit schreiben"
sudo tee /etc/systemd/system/parking-backend.service >/dev/null <<'EOF'
[Unit]
Description=Parking FastAPI backend (Uvicorn)
After=network.target

[Service]
User=%i
WorkingDirectory=/var/www/parking
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/var/www/parking/backend/.env
ExecStart=/var/www/parking/.venv/bin/python -m uvicorn backend.server:app --host 127.0.0.1 --port 8001 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo sed -i "s/User=%i/User=$USER/" /etc/systemd/system/parking-backend.service

sudo systemctl daemon-reload
sudo systemctl enable parking-backend
sudo systemctl restart parking-backend
sleep 1
sudo systemctl --no-pager status parking-backend || true

echo "[5/6] Nginx-Site für API"
sudo tee /etc/nginx/sites-available/api.gashis.ch >/dev/null <<'EOF'
server {
    listen 80;
    server_name api.gashis.ch;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/api.gashis.ch /etc/nginx/sites-enabled/api.gashis.ch
sudo nginx -t
sudo systemctl reload nginx

echo "[6/6] Certbot TLS für api.gashis.ch (falls noch nicht vorhanden)"
if ! sudo test -e /etc/letsencrypt/live/api.gashis.ch/fullchain.pem; then
  sudo certbot --nginx -d api.gashis.ch --redirect -m admin@${HOSTNAME} --agree-tos -n || true
fi

echo "Fertig: Backend sollte unter https://api.gashis.ch/ erreichbar sein."
EOSSH
