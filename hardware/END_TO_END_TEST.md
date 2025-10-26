# End‑to‑End Test – Smart Parking

Kurzleitfaden: Flash → Health → Hall‑Event → Backend‑POST prüfen.

## Voraussetzungen
- Backend läuft lokal (FastAPI auf Port 8000) und liefert `/health` = 200.
- Optional: Cloudflare Quick Tunnel aktiv (öffentliche trycloudflare‑URL).
- Verkabelung gemäß Variante A (mit oder ohne DC‑Stecker). GND gemeinsam.

## 1) Firmware flashen
- WiFi: `hardware/smart_parking_all_in_one.ino`
  - WLAN optional: `WIFI_SSID/PASS` setzen.
  - `BACKEND_BASE` = LAN‑IP deines Rechners, z. B. `http://192.168.1.23:8000`.
- LTE: `hardware/smart_parking_sim7600_all_in_one.ino`
  - `APN=gprs.swisscom.ch`, `SERVER_HOST=<deine-trycloudflare-Domain>`, `USE_HTTPS=1`.
  - UART: SIM7600 TX→GPIO16, RX→GPIO17.

## 2) Start überprüfen (serieller Monitor)
- Baudrate: 115200.
- Erwartet: Bootmeldungen, initialer Status („occupied“/„free“), ggf. WiFi/IP oder Modem‑Infos.

## 3) Health‑Check
- Lokal: `curl http://127.0.0.1:8000/health` → `OK` / HTTP 200.
- Über Tunnel: `curl https://<dein>.trycloudflare.com/health` → `OK` / HTTP 200.
- LTE‑Variante macht periodische Health‑Pings (Standard: 60 s).

## 4) Hall‑Event auslösen
- Magnet an den Hall‑Sensor halten bzw. entfernen.
- Serieller Monitor: Statuswechsel → „occupied“/„free“ geloggt.
- Servo bewegt sich zwischen OPEN_ANGLE/CLOSED_ANGLE.

## 5) Backend‑POST verifizieren
- WiFi: bei Statuswechsel `PUT /parking-spots/{id}/status` (HTTP 200 erwartet).
- LTE: `POST /parking-spots/{id}/status` (HTTP 200 erwartet).
- Backend‑Konsole/Logs prüfen; alternativ im UI/DB (falls vorhanden) den Status sehen.

## Troubleshooting
- Keine 200 auf /health: Backend nicht gestartet oder Port geblockt.
- Keine WiFi‑Verbindung: SSID/PASS, Empfang, IP‑Bereich prüfen.
- Kein LTE: APN/Signal/Antennen/UART Pins checken.
- Servo zuckt: 5‑V‑Rail prüfen, GND gemeinsam, optional Pufferkondensatoren.
- CORS/Frontend: Für reine Firmware‑Tests nicht relevant; nur nötig fürs Web UI.
