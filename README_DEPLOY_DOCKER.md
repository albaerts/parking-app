Docker Compose + CI/CD Deploy (Empfohlener Weg)
===============================================

Kurz: Dieses Repo enthält jetzt Beispiel-Dockerfiles für Backend und Frontend und ein `docker-compose.yml`.
Die GitHub Actions-Workflow (`.github/workflows/docker-deploy.yml`) baut das Frontend und führt optional einen Deploy-Schritt via SSH aus (benötigt Secrets).

Schnellstart (lokal)
--------------------
Voraussetzungen: Docker & Docker Compose installiert.

1) Baue und starte lokal:

```bash
# Im Projekt-Root
docker-compose build
docker-compose up -d

# Backend sollte unter http://localhost:8000 erreichbar sein
# Frontend (React) wird unter http://localhost:3000 serviert (nginx)
```

Hinweis zu SQLite: das `docker-compose.yml` mountet `./backend/parking.db` in den Container, damit die DB persistent ist. Falls die Datei nicht existiert, wird sie beim ersten Start erzeugt.

GitHub Actions Deploy (SSH)
---------------------------
Die Action `docker-deploy.yml` macht folgendes:
- baut das Frontend und installiert Backend-Abhängigkeiten (für sanity checks)
- wenn Secrets gesetzt sind, kopiert das Repo via SCP auf den Zielserver und führt remote `docker-compose up -d --build`

Benötigte Secrets (Repository settings -> Secrets):
- SSH_HOST: Zielserver IP oder Hostname
- SSH_USER: Benutzername auf dem Zielserver (z.B. deploy)
- SSH_PRIVATE_KEY: Private SSH Key (ohne Passwort) für den oben genannten Benutzer
- SSH_PORT (optional): SSH Port, default 22
- REMOTE_PATH: Zielpfad auf Server, z.B. `/var/www/parkingsrv`

Empfohlene Server-Vorbereitung
-----------------------------
Auf dem Server (einmalig):

```bash
# als root oder sudo
apt update && apt install -y docker.io docker-compose git
usermod -aG docker $USER  # so kann deploy docker nutzen
mkdir -p /var/www/parkingsrv
chown deploy:deploy /var/www/parkingsrv
```

Dann kannst du die GitHub Action nutzen, um bei jedem Push auf `main` automatisch zu deployen.

Wichtige Hinweise und Fortgeschrittenes
--------------------------------------
- In Produktion ist SQLite nur bedingt geeignet; wenn du mehrere Backend-Instanzen planst oder stabilen DB-Betrieb willst, wechsele auf PostgreSQL.
- Für zero-downtime und bessere Rollbacks ist ein Registry-basierter Workflow (Image -> Registry -> Server zieht Image) besser. Die jetzige Action kopiert das Repo direkt.
- Setze SSL (nginx / Let's Encrypt) auf dem Server, wenn du den Frontend-Port öffentlich bereitstellst.
 
Registry-basiertes Deploy (Aktualisiert)
--------------------------------------
In dieser Version unterstützen wir ein Registry-basiertes Deploy: die GitHub Actions bauen Images und pushen sie zu GitHub Container Registry (GHCR) unter `ghcr.io/<owner>/parking-backend` und `ghcr.io/<owner>/parking-frontend`.

Benötigte (Repo)Secrets für Registry/Deploy:
- `GITHUB_TOKEN` (wird automatisch zur Verfügung gestellt und wird für GHCR-Login verwendet)
- `SSH_HOST` – Server Hostname/IP
- `SSH_USER` – SSH User (z.B. `deploy`)
- `SSH_PRIVATE_KEY` – Private SSH key content (no passphrase)
- `REMOTE_PATH` – Pfad zum Deployment-Ordner auf dem Server (z.B. `/var/www/parkingsrv`)
- optional: `SSH_PORT`

Wie es funktioniert auf dem Server:
- Wir empfehlen, im `REMOTE_PATH` eine Datei `docker-compose.prod.yml` zu haben (liegt im Repo). Diese Datei referenziert die Images `ghcr.io/<owner>/parking-backend:<IMAGE_TAG>` und `ghcr.io/<owner>/parking-frontend:<IMAGE_TAG>`.
- Die Action pulled die neuen Images und führt `docker-compose -f docker-compose.prod.yml up -d` aus.

Vorteile dieses Ansatzes:
- Reproduzierbare Images (keine Abhängigkeit von Host-Builds)
- Schnelle Rollbacks (pull older image tag and re-run compose)
- CI sorgt für konsistente Builds

Hinweis zu `IMAGE_TAG`:
- Die Action setzt `IMAGE_TAG` auf die Commit SHA. Auf dem Server wird das `docker-compose.prod.yml` genutzt und die Action führt `docker pull` für das Tag, danach `docker-compose up -d`.

Wenn du möchtest, kann ich jetzt:
1) `docker-compose` näher an deine Server-Ordnerstruktur anpassen (z.B. mount log- & config-Pfade),
2) die GitHub Actions so erweitern, dass sie Image in eine Registry pushed (erledigt), oder
3) ein Beispiel `docker-compose.prod.yml` mit nginx reverse-proxy + certbot hinzufügen.

Quick server steps to use the deploy helper
-----------------------------------------
Once the images are pushed and your server has Docker & Docker Compose, do the following on the server:

```bash
# clone repo into REMOTE_PATH (if not already)
git clone <repo> /var/www/parkingsrv
cd /var/www/parkingsrv

# make deploy script executable
chmod +x deploy/update.sh

# Run deploy helper with the image tag pushed by CI (CI uses commit SHA by default)
# Example using SHA from CI: ./deploy/update.sh 012345abcdef
./deploy/update.sh <IMAGE_TAG>
```

TLS / Let's Encrypt notes
-------------------------
The `docker-compose.prod.yml` includes a `proxy` (nginx) service that mounts a sample config `deploy/nginx.conf`. For TLS you need certificates under `deploy/certs` mounted into `/etc/letsencrypt` inside the container.

Two practical ways to get certs:
- Run `certbot` on the host and copy `/etc/letsencrypt` into `deploy/certs` (then mount read-only). This is simple and robust.
- Use a containerized Let's Encrypt companion (e.g. `nginx-proxy` + `letsencrypt-nginx-proxy-companion`), but that requires additional compose services and DNS configuration.

If du willst, implementiere ich gern die certbot-on-host Variante mit a) anweisungen und b) ein kleines script `deploy/refresh-certs.sh` to sync certs into the repo (only if you want).

Sag kurz, welche Erweiterung du willst, dann implementiere ich sie.