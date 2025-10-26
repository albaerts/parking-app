#!/usr/bin/env bash
set -euo pipefail

# Debian 12 (bookworm) Grundsetup für VPS
# – installiert Nginx, Certbot, Python, ufw (optional) und legt /var/www/parking an

if [[ $(id -u) -ne 0 ]]; then
  echo "Bitte als root ausführen: sudo ./deploy/prepare_server_debian.sh" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt update
apt -y upgrade
apt -y install nginx certbot python3-certbot-nginx python3-venv python3-pip git curl rsync

# Firewall optional einrichten
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 'Nginx Full' || true
  yes | ufw enable || true
fi

mkdir -p /var/www/parking
chown ${SUDO_USER:-$USER}:${SUDO_USER:-$USER} /var/www/parking

echo "Server vorbereitet. Stelle sicher, dass DNS A-Records gesetzt sind:"
echo "  - api.gashis.ch     -> <SERVER_IP> (fürs Backend)"
echo "  - parking.gashis.ch -> <SERVER_IP> (fürs Frontend)"
