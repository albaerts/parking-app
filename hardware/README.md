# Smart Parking Hardware – Kurzanleitung

Diese Anleitung fasst die wichtigsten Schritte zusammen: Verdrahtung, Test, All-in-One Firmware, Kalibrierung und Backend-Anbindung.

## Komponenten
- ESP32 DevKit (z. B. DOIT)
- SG92R (9g) Servo – 5V Versorgung (z. B. Pololu S13V20F5)
- Hall-Sensor A3144 (mit 10k Pull-up intern)
- Status-LED + 220–330 Ohm (optional, GPIO 2)
- 2× 18650 + Halterung (oder Netzteil)
- Gemeinsame Masse (GND!)

## Pins (Standard-Setup)
- Servo: Signal → GPIO 18, +5V → 5V, GND → GND
- Hall-Sensor: Signal → GPIO 19, VCC → 3V3, GND → GND
- LED (optional): Anode → 220Ω → GPIO 2, Kathode → GND

Siehe auch `WIRING_A4.md` für eine A4-Ansicht mit Farbcodes.

## Schritt 1: Einzeltests
1) Servo-Test: `hardware/servo_test.ino` flashen
   - Prüfen, ob der Arm ruhig zwischen zwei Winkeln schwenkt
2) Hall-Test: `hardware/hall_sensor_test.ino` flashen
   - Magnet oder Rad in Sensor-Nähe: Serieller Monitor zeigt Zustandswechsel

## Schritt 2: All-in-One Firmware
- Datei: `hardware/smart_parking_all_in_one.ino`
- Passt Servo + Hall + LED + optional WiFi/Backend zusammen.

Wichtige Parameter (oben in der Datei):
- CLOSED_ANGLE / OPEN_ANGLE: Winkel kalibrieren (Barriere zu/auf)
- WIFI_SSID / WIFI_PASS: leer lassen = offline
- BACKEND_BASE: Lokale Backend-IP setzen, z. B. `http://192.168.1.23:8000`
- PARKING_SPOT_ID: Spot-ID, der im Backend aktualisiert werden soll

Hinweis: 127.0.0.1 (localhost) funktioniert NICHT auf dem ESP32. Verwende die LAN-IP deines Rechners.

## Schritt 3: Kalibrierung
- Servo mechanisch so montieren, dass bei CLOSED_ANGLE sicher blockiert wird
- Bei OPEN_ANGLE soll die Durchfahrt frei sein
- Falls Servo pulsiert: min/max Pulsweite in `attach()` anpassen (z. B. 500–2500 µs)

## Schritt 4: Backend-Anbindung (optional)
- Backend lokal starten (läuft auf Port 8000)
- Stelle sicher, dass das Frontend auf `http://localhost:3000/parking` erreichbar ist
- ESP32 verbindet sich per WiFi mit `BACKEND_BASE` und sendet `PUT /parking-spots/{id}/status`
  - Payload: `{ "status": "free" | "occupied" }`

## Sicherheit & Strom
- Servo braucht Spitzenstrom: separate 5V-Versorgung empfohlen
- Masse (GND) immer gemeinsam verbinden
- Keine 9V-Blockbatterie für Servo – zu schwach/instabil

## Troubleshooting
- Servo zuckt: eigene 5V-Versorgung, GNDs verbinden, 50 Hz nutzen
- Hall invertiert: Konstanten in der Firmware prüfen (`HALL_LOW_IS_OCCUPIED`)
- Keine Backend-Updates: IP korrekt? WLAN verbunden? Backend erreichbar? CORS ok?
- ESP32 stürzt bei WiFi ab: erst offline testen, dann WiFi schrittweise aktivieren

Viel Erfolg beim Aufbau! 🚗

## SIM/LTE Variante (SIM7600)

- Sketch: `hardware/smart_parking_sim7600_all_in_one.ino`
- Verkabelung (üblich, anpassbar):
   - SIM7600 TX → ESP32 RX (GPIO 16)
   - SIM7600 RX → ESP32 TX (GPIO 17)
   - SIM7600 VCC → passende Versorgung (5–9V, 2A Peak), GND → GND
   - Gemeinsame Masse mit ESP32/Servo
- APN eintragen: `APN`, ggf. `GPRS_USER`/`GPRS_PASS`
- Backend erreichbar machen:
   - Entweder Backend auf einem Server mit öffentlicher IP/Domain betreiben
   - Oder lokalen Backend-Port 8000 via Tunnel öffentlich machen (z. B. Cloudflare Tunnel)
   - Im Sketch `SERVER_HOST` (Domain/IP) und `SERVER_PORT` setzen
- Die Firmware sendet per HTTP `POST /parking-spots/{id}/status` mit `{ "status": "free"|"occupied" }`
- Für HTTPS: auf `TinyGsmClientSecure` umstellen und Port 443 nutzen (Zertifikatsanforderungen beachten)
