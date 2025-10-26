# Assembly Quickstart – Variante A (Powerbank + PD‑Trigger)

Stand: 18.10.2025 · Diese Anleitung führt dich Schritt für Schritt durch den Aufbau der Stromversorgung und Verdrahtung mit Powerbank + USB‑C PD‑Trigger für den Smart‑Parking‑Prototyp.

Siehe auch:
- Verdrahtungs‑Übersicht (A4 + SVG): `hardware/WIRING_ESP32_SIM7600A_A4.md`
- Einkaufsliste/Links (CH): `DIGITEC_BESTELLHILFE_ZUERICH.md` (Artikel 10 + WAGO‑Klemmen)
- Firmware (WiFi): `hardware/smart_parking_all_in_one.ino`
- Firmware (LTE/SIM): `hardware/smart_parking_sim7600_all_in_one.ino`

## Zielbild

- 5 V/3 A aus Powerbank → PD‑Trigger → 5‑V‑Verteiler (WAGO 221) → SIM7600 HAT, Servo, optional ESP32 VIN
- Alle Massen (GND) gemeinsam, kurze Leitungen, eindeutige Farbcodierung (Rot = +5 V, Schwarz = GND)

## Benötigte Teile (Variante A)

Pflicht:
- USB‑C Powerbank (ca. 20.000 mAh) mit Power Delivery (≥18 W)
- USB‑C PD‑Trigger (fix 5 V, bis 3 A) + USB‑C ↔ USB‑C Kabel (mind. 60 W, e‑marked)
- DC‑Stecker 5.5×2.1 mm (Schraubklemmen) ODER direkt Litzen vom PD‑Trigger in WAGO
- 2× WAGO 221‑415 (5‑polig) als 5‑V‑ und GND‑Bus
- Silikonlitzen (Rot/Schwarz) 0.5–1.0 mm² (AWG 20–18)
- ESP32 DevKit + Servo (SG90/SG92R) + Hall‑Sensor A3144
- SIM7600 HAT A (UART‑Variante) – nur für LTE‑Betrieb notwendig

Optional (bei Instabilitäten/Resets):
- 1000 µF / 25 V Low‑ESR Elko nahe SIM7600 HAT (Plus an +5 V, Minus an GND)
- 330–470 µF / 25 V Elko nahe Servo + 100 nF Keramik (X7R) parallel

Sicherheit:
- Immer stromlos arbeiten. Polung (+/–) vor jedem Einschalten prüfen. Keine 3.3‑V‑Pins für Servo‑Versorgung verwenden.

## Schritt 1 – PD‑Trigger vorbereiten und testen

1. Powerbank einschalten und über USB‑C Kabel mit dem PD‑Trigger verbinden.
2. Falls vorhanden: Multimeter an den Ausgang des PD‑Triggers (Vout/GND) halten → ~5.0 V messen.
3. Einige Trigger haben LEDs/Displays (z. B. „5.0 V“): prüfen, dass 5 V ausgehandelt sind.

Hinweis: Falls keine 5 V anliegen, anderes USB‑C Kabel probieren (e‑marked) oder Powerbank‑Taste drücken (manche gehen in Standby ohne Last).

## Schritt 2 – DC‑Stecker/Versorgungsausgang herstellen

Variante A (mit DC‑Stecker):
- Plus (rot) vom PD‑Trigger in „+“ des Schraub‑DC‑Steckers klemmen, Minus (schwarz) in „–“.
- Stecker später in ein Gegenstück (z. B. Panel‑Buchse) oder direkt als Speisezuleitung in die WAGO einsetzen.

Variante B (ohne DC‑Stecker):
- Die beiden Ausgangslitzen (Vout/GND) vom PD‑Trigger direkt in die WAGO‑Klemmen führen (siehe Schritt 3).

## Schritt 3 – 5‑V‑ und GND‑Bus mit WAGO 221 aufbauen

1. Zwei WAGO 221‑415 bereitlegen: eine als +5‑V‑Bus, eine als GND‑Bus.
2. Eingang vom PD‑Trigger (rot = +5 V) in die +5‑V‑WAGO, (schwarz = GND) in die GND‑WAGO.
3. Reserve‑Ports bleiben für Abgänge (SIM7600 HAT, Servo, ESP32 VIN).
4. Litzen sauber abisolieren (~11 mm), fest einstecken, Zugprobe machen.

Tipp: Hauptzuleitung vom PD‑Trigger in 0.75–1.0 mm², Abgänge in 0.5–0.75 mm² halten.

## Schritt 4 – Komponenten anschließen

Gemeinsame Regeln:
- Alle Massen GND verbinden (SIM7600, ESP32, Servo, Hall). Farbcode konsequent nutzen.
- Leitungen kurz halten, besonders zum Servo und zum HAT.

SIM7600 HAT A (LTE):
- VCC des HAT an +5‑V‑Bus, GND an GND‑Bus.
- UART: SIM7600 TX → ESP32 RX2 (GPIO 16), SIM7600 RX → ESP32 TX2 (GPIO 17).
- Antennen korrekt anstecken (LTE/Main, ggf. DIV/GNSS wie benötigt).

ESP32 DevKit:
- Variante 1 (über VIN speisen): VIN an +5‑V‑Bus, GND an GND‑Bus.
- Variante 2 (USB‑Kabel): ESP32 über USB vom Rechner versorgen; GND trotzdem mit dem 5‑V‑GND‑Bus verbinden.

Servo (SG90/SG92R):
- Rot an +5‑V‑Bus, Braun/Schwarz an GND‑Bus, Orange/Weiß (Signal) an ESP32 GPIO 18.
- Achtung: Servo NIEMALS an 3.3 V betreiben.

Hall‑Sensor A3144:
- VCC an 3.3 V (vom ESP32), GND an GND, OUT an ESP32 GPIO 19.
- Interner Pull‑up wird in der Firmware genutzt; gemeinsame Masse sicherstellen.

Optional: Pufferkondensatoren
- 1000 µF/25 V am HAT (zwischen +5 V und GND, Polung beachten), 330–470 µF/25 V am Servo.
- Zusätzlich je 100 nF Keramik nahe der Verbraucher parallel.

## Schritt 5 – Mechanik & Zugentlastung

- PD‑Trigger und WAGOs auf einer Platte fixieren (Klebepad/Schrauben). 
- Litzen so verlegen, dass Servobewegungen keine Zugspannung erzeugen.
- Kabelbinder oder Spiralband zur Bündelung nutzen.

## Erstinbetriebnahme – Checks

- Vor dem Einschalten alle Verbindungen und Polung prüfen.
- Powerbank einschalten → PD‑Trigger zeigt 5.0 V an (oder 5.0 V messen).
- ESP32 startet (Power‑LED), SIM7600 HAT ggf. mit Status‑LEDs.

Wenn der ESP32 über USB mit dem PC verbunden ist: Seriellen Monitor öffnen (115200 Baud) und Bootlogs prüfen.

## Kurztest – Funktion

Variante WiFi (ohne SIM):
1. `hardware/smart_parking_all_in_one.ino` flashen.
2. Werte oben in der Datei setzen (WIFI_SSID/WIFI_PASS optional, BACKEND_BASE = LAN‑IP deines Rechners, z. B. `http://192.168.1.23:8000`).
3. Nach dem Start sollte der Servo kurz kalibrieren/sich bewegen. Den Hall‑Sensor mit Magnet betätigen → Statuswechsel im seriellen Monitor.

Variante LTE/SIM (mit SIM7600):
1. `hardware/smart_parking_sim7600_all_in_one.ino` flashen.
2. `APN` (z. B. Swisscom: `gprs.swisscom.ch`) setzen. `SERVER_HOST` auf deine aktuelle Quick‑Tunnel‑Domain (z. B. `https://<dein-trycloudflare>.trycloudflare.com`). `USE_HTTPS=1` belassen.
3. Seriellen Monitor (115200 Baud) öffnen → warten bis Netzregistrierung ok, dann Health‑Ping → `200` erwartet.
4. Hall‑Sensor betätigen → Firmware sendet Status `POST` an Backend; im Backend‑Log sollte ein Request sichtbar sein.

Hinweis: Lokales Backend erreichbar machen (Port 8000) und optional via Cloudflare Quick Tunnel veröffentlichen. Der Health‑Check `/health` muss `200 OK` liefern.

## Troubleshooting

- Servo zuckt oder ESP32 resetet:
  - Separate 5‑V‑Rail vorhanden? GNDs gemeinsam? Optional Elkos nahe HAT/Servo ergänzen.
  - Leitungen kürzen, AWG/Querschnitt erhöhen, gute USB‑C Kabel/Powerbank nutzen.
- Keine 5 V am PD‑Trigger: anderes e‑marked Kabel versuchen; Powerbank evtl. im Standby.
- SIM7600 verbindet nicht:
  - APN korrekt? Antenne korrekt? Signalstärke am Aufstellort? UART‑Pins (16/17) vertauscht?
- Backend Endpunkte nicht erreichbar:
  - Tunnel‑Domain aktuell? `/health` liefert 200? CORS/Ports korrekt?

## Nächste Schritte

- Firmware‑Parameter feinjustieren (OPEN/CLOSED_ANGLE, Debounce Hall etc.).
- Mechanische Montage finalisieren (Servohorn/Barriere), Kabelschutz.
- Optional: Foto/Skizze deines Aufbaus in `hardware/` ablegen, um die Dokumentation zu ergänzen.

Viel Erfolg beim Aufbau! 🚗
