#!/usr/bin/env bash
set -euo pipefail

# recover_proxy.sh
# Zweck: Proxy/Ports schnell diagnostizieren und zwischen TLS/HTTP-only umschalten.
# Nutzung:
#   ./deploy/recover_proxy.sh diag          # Diagnose (docker ps, Ports, Logs, Certs, nginx -t)
#   ./deploy/recover_proxy.sh http-fallback # Schnell online auf Port 80 (ohne TLS)
#   ./deploy/recover_proxy.sh tls-restore   # Zurück zu TLS (deploy/nginx.conf), Port 443/80
#   ./deploy/recover_proxy.sh restart       # Proxy sauber neu starten
# Optional: Argument --post-diag, um nach einer Aktion auch Diagnose auszugeben
#   z.B.: ./deploy/recover_proxy.sh http-fallback --post-diag

POST_DIAG=0
if [[ ${2:-} == "--post-diag" ]]; then
  POST_DIAG=1
fi

DC="docker compose"
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
fi

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

stop_host_nginx() {
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet nginx; then
      echo "[host] nginx läuft -> stoppe und deaktiviere"
      sudo systemctl stop nginx || true
      sudo systemctl disable nginx || true
    else
      echo "[host] nginx ist nicht aktiv"
    fi
  else
    echo "[host] systemctl nicht verfügbar – überspringe host nginx check"
  fi
}

compose_ps() {
  $DC -f docker-compose.prod.yml ps || true
}

restart_proxy() {
  echo "[compose] Proxy neustarten"
  $DC -f docker-compose.prod.yml up -d --force-recreate proxy
}

make_http_override() {
  local override_file="docker-compose.override.yml"
  cat >"${override_file}" <<'YAML'
services:
  proxy:
    volumes:
      - ./deploy/nginx.http.conf:/etc/nginx/conf.d/default.conf:ro
YAML
  echo "[compose] ${override_file} geschrieben (HTTP-only Fallback aktiv)"
}

remove_http_override() {
  local override_file="docker-compose.override.yml"
  if [[ -f "${override_file}" ]]; then
    mv "${override_file}" "${override_file}.bak.$(date +%s)"
    echo "[compose] ${override_file} entfernt (TLS-Config wieder aktiv)"
  else
    echo "[compose] kein ${override_file} gefunden"
  fi
}

check_certs() {
  local cert_dir="/etc/letsencrypt/live/parking.gashis.ch"
  if [[ -r "${cert_dir}/fullchain.pem" && -r "${cert_dir}/privkey.pem" ]]; then
    echo "[certs] Zertifikate vorhanden: ${cert_dir}/fullchain.pem, privkey.pem"
    ls -l "${cert_dir}"/*.pem || true
  else
    echo "[certs] Zertifikate fehlen oder nicht lesbar unter ${cert_dir}"
    return 1
  fi
}

case "${1:-}" in
  diag)
    ./deploy/diag_proxy.sh
    ;;
  http-fallback)
    stop_host_nginx
    make_http_override
    restart_proxy
    if [[ ${POST_DIAG} -eq 1 ]]; then ./deploy/diag_proxy.sh; fi
    ;;
  tls-restore)
    stop_host_nginx
    check_certs || echo "[warn] TLS-Zertifikate nicht gefunden – TLS wird vermutlich nicht starten"
    remove_http_override
    restart_proxy
    if [[ ${POST_DIAG} -eq 1 ]]; then ./deploy/diag_proxy.sh; fi
    ;;
  restart)
    stop_host_nginx
    restart_proxy
    if [[ ${POST_DIAG} -eq 1 ]]; then ./deploy/diag_proxy.sh; fi
    ;;
  *)
    echo "Nutzung: $0 {diag|http-fallback|tls-restore|restart} [--post-diag]" >&2
    exit 2
    ;;
 esac
