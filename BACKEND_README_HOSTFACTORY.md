# Deployment ohne Cloudflare: Direkt über Hostfactory (A-Record + Nginx + Let’s Encrypt)

Dieses Setup nutzt Hostfactory nur für DNS und Hosting/Server. Du brauchst entweder:
- einen Managed Server/VPS mit Root-Zugriff (empfohlen), oder
- die Möglichkeit, Nginx/Certbot zu betreiben und Ports 80/443 freizugeben.

Shared Webhosting (nur PHP) reicht für FastAPI nicht – dort können keine dauerhaften Python-Dienste laufen.

## Überblick
- DNS: A/AAAA-Record für `api.gashis.ch` zeigt auf die öffentliche IP deines Servers.
- Nginx: Terminiert TLS (Let’s Encrypt) und proxyt Anfragen zu FastAPI (127.0.0.1:8000).
- Uvicorn (systemd): Startet die API als Dienst.

## 1) DNS bei Hostfactory
- Setze bei `api.gashis.ch` einen A-Record auf die öffentliche Server-IP.
- Optional AAAA-Record für IPv6.
- Warte bis TTL abgelaufen ist (wenige Minuten bis 1h).

## 2) Nginx und Certbot installieren (Debian/Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

## 3) vHost bereitstellen
```bash
# vHost-Datei kopieren
sudo cp infra/nginx/api.gashis.ch.conf /etc/nginx/sites-available/api.gashis.ch
sudo ln -s /etc/nginx/sites-available/api.gashis.ch /etc/nginx/sites-enabled/api.gashis.ch

# Testen & reload
sudo nginx -t && sudo systemctl reload nginx
```

## 4) TLS-Zertifikat via Let’s Encrypt
```bash
sudo certbot --nginx -d api.gashis.ch --agree-tos -m you@example.com --redirect
```
- Certbot ergänzt die ssl_certificate-Pfade automatisch im vHost.
- Auto-Renewal ist per Timer aktiv (`systemctl list-timers`).

## 5) FastAPI als Dienst starten
```bash
# Abhängigkeiten installieren (einmalig)
cd backend
pip install -r requirements.txt

# systemd-Service anpassen (Pfad/Benutzer)
sudo cp backend/uvicorn.service /etc/systemd/system/uvicorn.service
sudo sed -i 's|/opt/parking-app/backend|'"$(pwd)"'|g' /etc/systemd/system/uvicorn.service
sudo systemctl daemon-reload
sudo systemctl enable --now uvicorn

# Status prüfen
systemctl status uvicorn --no-pager
```

## 6) Funktionstest
```bash
# Lokal auf dem Server
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/api/health

# Über Domain (extern)
curl -i https://api.gashis.ch/health
curl -i https://api.gashis.ch/api/health
```
Erwartet ist 200 OK für beide Endpunkte.

## Hinweise
- Wenn du nur Shared Hosting hast (kein Root):
  - FastAPI kann dort nicht dauerhaft laufen. Du brauchst einen VPS/Managed Server (bei Hostfactory oder anderswo) oder alternativ den zuvor beschriebenen Cloudflare Tunnel von einem beliebigen Rechner/Server.
- CORS: Das Backend erlaubt u.a. `https://gashis.ch` – dein Frontend kann also aus der Hauptdomain auf `https://api.gashis.ch` zugreifen.
- SIM7600/TLS: Wir erzwingen TLS1.2/SNI serverseitig; das Modem ist tolerant konfiguriert (kein Zertifikats-Check in der Firmware). Nginx-Standardciphers funktionieren.
