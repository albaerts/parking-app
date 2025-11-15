# Produktions-Deployment Anleitung (Deutsch)

Diese Anleitung zeigt zwei Wege, deine App auf den Server zu bringen:
1. CI / GitHub Actions (automatisch bei Push auf `main`)
2. Manueller SSH-Deploy von deinem lokalen Rechner

---
## 1. Voraussetzungen auf dem Server

```bash
# Einmalig als root oder via sudo
apt update && apt -y upgrade
apt -y install docker.io docker-compose git curl wget rsync
usermod -aG docker deploy   # falls 'deploy' dein User ist
mkdir -p /var/www/parkingsrv
chown deploy:deploy /var/www/parkingsrv
```

DNS: `parking.gashis.ch` zeigt auf die Server-IP.

TLS Zertifikate (optional zuerst HTTP testen):
- Mit certbot host-basiert: `apt install certbot python3-certbot-nginx`
- Dann `certbot certonly --standalone -d parking.gashis.ch --agree-tos -m admin@parking.gashis.ch`
- Zertifikate liegen unter `/etc/letsencrypt`; Compose mountet sie in den Proxy.

---
## 2. GitHub Secrets einrichten (CI-Weg)
In den Repository-Einstellungen unter `Settings -> Secrets and variables -> Actions` folgende Secrets setzen:

| Secret            | Bedeutung                          |
|-------------------|------------------------------------|
| SSH_HOST          | Server Host/IP                     |
| SSH_USER          | SSH Benutzer (z.B. deploy)         |
| SSH_PRIVATE_KEY   | Privater Key (ohne Passwort)       |
| REMOTE_PATH       | Zielpfad (z.B. /var/www/parkingsrv)|
| GHCR_PAT (optional)| Falls GHCR private Images pullen muss |

Bei Push auf `main` baut der Workflow:
- Backend Image: `ghcr.io/<owner>/parking-backend:<sha>`
- Frontend Image: `ghcr.io/<owner>/parking-frontend:<sha>`
- Führt remote `deploy/update.sh <sha>` aus

---
## 3. Server Umgebung (.env)
Erstelle `/var/www/parkingsrv/.env.prod` (oder exportiere die Variablen in die Shell vor Compose):

```env
JWT_SECRET=dein_langer_geheimer_string
DATABASE_URL=postgresql+psycopg2://parking:parking_pass@postgres:5432/parkingdb
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
MAIL_FROM=no-reply@parking.gashis.ch
AUTO_VERIFY_ON_EMAIL_FAILURE=false
POSTGRES_USER=parking
POSTGRES_PASSWORD=parking_pass
POSTGRES_DB=parkingdb
```

Dann: `export $(grep -v '^#' .env.prod | xargs)` oder verwende ein Systemd EnvironmentFile.

---
## 4. Manuelles Deployment (lokal build & push)
Falls du ohne CI testen willst:

```bash
# Im Projekt-Root lokal
# Backend Image bauen & pushen
REGISTRY=ghcr.io OWNER=albaerts TAG=manual$(date +%s)

docker build -f backend/Dockerfile -t $REGISTRY/$OWNER/parking-backend:$TAG .
docker push $REGISTRY/$OWNER/parking-backend:$TAG

docker build -f frontend/Dockerfile -t $REGISTRY/$OWNER/parking-frontend:$TAG .
docker push $REGISTRY/$OWNER/parking-frontend:$TAG

# SSH auf Server und deploy starten
ssh deploy@$SSH_HOST "cd /var/www/parkingsrv && export IMAGE_TAG=$TAG REGISTRY=$REGISTRY REPO_OWNER=$OWNER && ./deploy/update.sh $TAG"
```

Health-Check:
```bash
curl -s https://parking.gashis.ch/api/autocomplete?q=B | head
```

Logs prüfen:
```bash
docker logs -f parking_backend
docker logs -f parking_proxy
```

---
## 5. Rollback
Vor dem Deploy legt das Script einen Backup-Branch an. Alternativ kannst du einen älteren Image-Tag ziehen:

```bash
export IMAGE_TAG=<ältere_commit_sha>
./deploy/update.sh $IMAGE_TAG
```

---
## 6. Datenbank Migrationen
Alembic ist eingerichtet:
```bash
# Neue Revision erzeugen nach Model-Änderung
docker-compose -f docker-compose.prod.yml run --rm backend alembic -c backend/alembic.ini revision --autogenerate -m "Änderung"
# Upgrade
docker-compose -f docker-compose.prod.yml run --rm backend alembic -c backend/alembic.ini upgrade head
```
Das Deploy-Script versucht immer zuerst Alembic und fällt dann (falls nötig) auf create_all zurück.

---
## 7. Zertifikate aktualisieren
Auf dem Server:
```bash
sudo ./deploy/refresh-certs.sh
./deploy/update.sh $IMAGE_TAG   # Proxy neu starten damit neue certs aktiv
```

---
## 8. Häufige Probleme
| Problem | Ursache | Lösung |
|---------|---------|--------|
| 502 Bad Gateway | Backend Container nicht healthy | `docker ps`, Healthcheck warten, Logs prüfen |
| Autocomplete 429 sofort | Zu viele Requests/Tests | Warte 60s, Rate Limit reset |
| Login 403 unverifiziert | Mail Versand fehlte | Azure Credentials setzen oder temporär `AUTO_VERIFY_ON_EMAIL_FAILURE=true` in Staging |
| Nginx zeigt nur Redirect | TLS fehlt / Port 443 blockiert | Certbot ausführen, Firewall-Regeln prüfen |

---
## 9. Nächste Härtungs-Schritte
- Content-Security-Policy Header prüfen (Inline Skripte entfernen)
- Fail2ban / access log pattern
- Beobachtung: Prometheus Endpoint für Metriken / Traefik alternative

Fertig. Bei Wunsch nach Automatisierung (Systemd Unit für `docker-compose` oder Prometheus Exporter) einfach melden.
