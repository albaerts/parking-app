#!/usr/bin/env bash
set -euo pipefail

# Cleanup-Skript: gibt schnell Speicher frei, ohne laufende Container zu zerstören.
# - Pruned nur UNBENUTZTE Images/Container/Volumes/Builder-Cache
# - Kürzt große Docker-JSON-Logs
# - Leert apt-Cache und optional Systemd-Journal (auf 7 Tage)

echo "[info] Platz vor Cleanup"
df -h || true
echo
echo "[info] Docker-Belegung vor Cleanup"
docker system df -v || true
echo

echo "[step] Unbenutzte Container entfernen"
docker container prune -f || true

echo "[step] Unbenutzte Images entfernen (kann mehrere GB freigeben)"
docker image prune -af || true

echo "[step] Builder-Cache entfernen"
docker builder prune -af || true

echo "[step] Unbenutzte Volumes entfernen (nicht verwendete Volumes, laufende bleiben erhalten)"
docker volume prune -f || true

echo "[step] Große Docker-JSON-Logs kürzen"
if [ -d /var/lib/docker/containers ]; then
  find /var/lib/docker/containers -type f -name "*-json.log" -exec truncate -s 0 {} \; || true
fi

echo "[step] apt-Cache leeren (Host)"
if command -v apt-get >/dev/null 2>&1; then
  apt-get clean || true
  rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* || true
fi

echo "[step] Systemd-Journal eindampfen (7 Tage)"
if command -v journalctl >/dev/null 2>&1; then
  journalctl --vacuum-time=7d || true
fi

echo
echo "[info] Docker-Belegung nach Cleanup"
docker system df -v || true
echo
echo "[info] Platz nach Cleanup"
df -h || true

echo
echo "[done] Cleanup abgeschlossen. Wenn weiterhin 'no space left on device' auftritt, prüfen Sie große Ordner mit:"
echo "       du -xh /var/lib/docker | sort -h | tail -n 50"
