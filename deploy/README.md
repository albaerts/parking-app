# Deploy-Anleitung (VPS)

Diese Anleitung bringt dein Backend (FastAPI) hinter Nginx mit TLS auf `api.gashis.ch` online und dein Frontend auf `parking.gashis.ch/parking/` (ohne Codeänderung). Es werden KEINE Benutzer erstellt oder geändert.

## Voraussetzungen
- Ubuntu 22.04/24.04 VPS, SSH-Zugang
- DNS A-Records zeigen auf den Server:
  - api.gashis.ch → <SERVER_IP>
  - parking.gashis.ch → <SERVER_IP>

## 0) Server vorbereiten (einmalig)
```
ssh <USER>@<SERVER>
sudo apt update && sudo apt -y upgrade
sudo apt -y install nginx certbot python3-certbot-nginx python3-venv python3-pip git curl
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
sudo mkdir -p /var/www/parking && sudo chown $USER:$USER /var/www/parking
```

## 1) Backend deployen (api.gashis.ch)
1. Variablen in `deploy/deploy_backend.sh` oben anpassen (SERVER, SSH_USER, REMOTE_DIR).
2. `.env` für das Backend vorbereiten (lokal oder per Editor auf dem Server):

```
JWT_SECRET=<ein_langer_geheimer_schlüssel>
MONGODB_URI=<deine_mongodb_uri>   # z.B. Atlas SRV
MONGODB_DB=parking
FORCE_MEMORY_MODE=0
SIMPLE_COMMAND_SECRET=<optional>
```

3. Skript lokal ausführen:
```
./deploy/deploy_backend.sh
```

Das Skript:
- rsync’t den Code nach `$REMOTE_DIR`
- erstellt/aktualisiert ein venv und installiert `backend/requirements.txt`
- schreibt die systemd-Unit und startet den Dienst
- installiert Nginx-Site für `api.gashis.ch`
- ruft Certbot für TLS auf

Check:
```
curl -s https://api.gashis.ch/api/health | jq
```

## 2) Frontend deployen (parking.gashis.ch/parking/)
Ohne Codeänderung wird das Frontend unter `/parking/` ausgeliefert (zu deiner aktuellen `homepage: "/parking"`).

1. Lokal bauen:
```
cd frontend
yarn install
yarn build
```
2. Hochladen & Nginx konfigurieren:
```
./deploy/deploy_frontend.sh
```

Das Skript kopiert `frontend/build/` nach `/var/www/parking/frontend_build/` und legt die Nginx-Site für `parking.gashis.ch` an (Root → 302 auf /parking/, Alias auf den Build).

Check:
- https://parking.gashis.ch/ → leitet auf /parking/
- https://parking.gashis.ch/parking/ → lädt App

## 3) Logs & Service
- Backend-Logs: `journalctl -u parking-backend -f --no-pager`
- Nginx Logs: `sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log`

## Hinweise
- Keine neuen Benutzer werden erstellt. Bestehende `@test.com`-User werden nicht verändert.
- Möchtest du die Subdomain auf Root nutzen (ohne `/parking/`), dann muss im Frontend `package.json` die `homepage` entfernt/angepasst und neu gebaut werden. Das ist optional und nicht Teil dieser Standard-Variante.
- Für Produktion mit PostgreSQL (empfohlen) solltest du ein Alembic Setup hinzufügen: `backend/alembic.ini`, ein `alembic/` Verzeichnis mit `env.py` und Migrationen. Danach kannst du Migrationen lokal erzeugen: `alembic revision --autogenerate -m "add field"` und deployseitig laufen lassen (`deploy/migrate_db.sh` nutzt Alembic automatisch, wenn verfügbar).

## Änderungen (automatisch angewendet)

- `docker-compose.prod.yml` wurde angepasst, sodass das gesamte `./backend` Verzeichnis in den Container gemountet wird (`./backend:/app/backend`). Das verhindert Probleme, bei denen `parking.db` als Verzeichnis existiert oder der Container-User keine Journals anlegen kann.
- `deploy/nginx.conf` wurde temporär auf HTTP-only gesetzt, damit der Proxy ohne TLS-Zertifikate startet. Für Produktion solltest du wieder die HTTPS-Variante verwenden und `/etc/letsencrypt` mounten.
- `deploy/update.sh` setzt standardmäßig `REPO_OWNER=albaerts` damit `docker pull` standardmäßig auf deinen GHCR-Namespace verweist.
- `backend/Dockerfile` setzt die Besitzrechte auf `/app/backend` beim Build, damit der non-root `appuser` Schreibzugriff hat.

Siehe Branch `deploy/fix-db-nginx` (erstellt und gepusht) für die Änderungen auf GitHub.
