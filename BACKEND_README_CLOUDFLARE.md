# Backend Bereitstellung mit Cloudflare Tunnel (api.gashis.ch)

Diese Anleitung verbindet api.gashis.ch sauber mit deinem FastAPI-Backend (port 8000) über einen Cloudflare Tunnel. TLS-Zertifikate werden automatisch gehandhabt, keine Ports müssen nach außen geöffnet werden.

## 1) DNS zu Cloudflare umziehen (einmalig)
- Erstelle die Zone gashis.ch im Cloudflare-Dashboard.
- Stelle die Nameserver bei Hostfactory auf die zwei von Cloudflare angezeigten Nameserver um.
- Warte, bis die Domain aktiv ist (meist < 1h).

## 2) cloudflared installieren und Tunnel einrichten
Auf dem Server, auf dem dein Backend läuft:

```bash
# cloudflared installieren (Linux x86_64 Beispiel)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Login (öffnet Browser / gibt URL aus)
cloudflared tunnel login

# Tunnel erstellen
cloudflared tunnel create smart-parking

# DNS-Eintrag für Hostname anlegen
auth_output=$(cloudflared tunnel route dns smart-parking api.gashis.ch || true)

echo "Erzeuge /etc/cloudflared/config.yml"
sudo mkdir -p /etc/cloudflared
sudo cp infra/cloudflared/config.yml /etc/cloudflared/config.yml

# Hinweis: Passe credentials-file in config.yml an die von cloudflared erstellte smart-parking.json an
# Beispiel-Pfad: /etc/cloudflared/<UUID>.json oder /etc/cloudflared/smart-parking.json

# Tunnel starten (Foreground-Test)
cloudflared tunnel run smart-parking
```

Wenn das funktioniert, als Dienst installieren:

```bash
# systemd Unit installieren
sudo cp infra/cloudflared/cloudflared.service /etc/systemd/system/cloudflared.service
sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared

# Status prüfen
systemctl status cloudflared --no-pager
```

## 3) Backend starten

```bash
# Python-Umgebung vorbereiten (einmalig)
cd backend
pip install -r requirements.txt

# Backend start (ohne Reload)
./start.sh

# oder mit Reload für Entwicklung
./start.sh --reload
```

## 4) Verifizieren

```bash
# Lokal
curl -i http://localhost:8000/health
curl -i http://localhost:8000/api/health

# Über Domain (Cloudflare)
curl -i https://api.gashis.ch/health
curl -i https://api.gashis.ch/api/health
```

Erwartet ist 200 OK für beide Health-Endpunkte. Die Firmware greift auf https://api.gashis.ch/api zu, daher ist /api/health besonders wichtig.

## Hinweise
- Wenn https://api.gashis.ch/api/health 404 liefert, läuft vermutlich ein anderer Dienst hinter Port 8000. Starte `backend/server.py` wie oben.
- Cloudflare SSL/TLS-Einstellung: „Full“ (oder „Full (strict)“ falls Origin-Zertifikat vorhanden).
- Optional: `SIMPLE_COMMAND_SECRET` setzen, wenn du die Dev-Queue-API schützen willst.
