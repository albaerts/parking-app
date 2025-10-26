#!/usr/bin/env bash
set -euo pipefail
SERVER="root@185.66.109.45"
REMOTE_BASE="/var/www/parking"
LOCAL_FRONTEND_DIR="./frontend"
LOCAL_BACKEND_DIR="./backend"
CERTBOT_EMAIL="albert@gashis.ch"
cd "$LOCAL_FRONTEND_DIR"
npm ci
PUBLIC_URL='/' npm run build
cd -
ssh $SERVER "mkdir -p ${REMOTE_BASE}/backup && cp -r ${REMOTE_BASE}/frontend_build ${REMOTE_BASE}/backup/frontend_build_$(date +%Y%m%d%H%M) || true"
rsync -avz --delete "${LOCAL_FRONTEND_DIR}/build/" ${SERVER}:${REMOTE_BASE}/frontend_build/
rsync -avz --delete "${LOCAL_BACKEND_DIR}/" ${SERVER}:${REMOTE_BASE}/backend/
ssh $SERVER bash -lc "cd ${REMOTE_BASE}/backend && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"
cat > /tmp/parking-backend.service <<'UNIT'
[Unit]
Description=Parking FastAPI backend
After=network.target
[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/parking/backend
Environment="PATH=/var/www/parking/backend/.venv/bin"
ExecStart=/var/www/parking/backend/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001 --workers 1
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
scp /tmp/parking-backend.service ${SERVER}:/etc/systemd/system/parking-backend.service
ssh $SERVER "systemctl daemon-reload && systemctl enable --now parking-backend && systemctl status parking-backend --no-pager || true"
ssh $SERVER "nginx -t && systemctl reload nginx || true"
ssh $SERVER "certbot --nginx -d parking.gashis.ch -d api.gashis.ch --non-interactive --agree-tos -m albert@gashis.ch" || true
ssh $SERVER "certbot renew --dry-run || true"
echo "Deploy fertig. Prüfe: https://parking.gashis.ch und https://api.gashis.ch/health"
