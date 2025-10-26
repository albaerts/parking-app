# Assembly Quickstart – Variante A ohne DC‑Stecker (direkt auf WAGO)

Stand: 18.10.2025 · Diese Anleitung zeigt die Powerbank + USB‑C PD‑Trigger Verkabelung ohne DC‑Hohlstecker. Die 5‑V‑Ausgänge des PD‑Triggers werden direkt in WAGO‑Klemmen geführt.

Siehe auch:
- Standard‑Anleitung mit DC‑Stecker: `hardware/ASSEMBLY_QUICKSTART_VAR_A.md`
- Verdrahtungs‑Übersicht (A4 + SVG): `hardware/WIRING_ESP32_SIM7600A_A4.md`
- Einkaufsliste/Links (CH): `DIGITEC_BESTELLHILFE_ZUERICH.md` (Artikel 10 + WAGO‑Klemmen)
 - Variante ohne DC‑Stecker (Wiring‑SVG, A4): `hardware/WIRING_ESP32_SIM7600A_NO_DC_A4.svg` (+ Druckhinweise in `WIRING_ESP32_SIM7600A_NO_DC_A4.md`)
 - Fotovorlage (A4) zum Abfotografieren deines Aufbaus: `hardware/PHOTO_TEMPLATE_NO_DC_A4.svg`

## Zielbild

- Powerbank → USB‑C PD‑Trigger → Vout (+) und GND (–) jeweils direkt in zwei WAGO 221‑415 → sternförmig zu SIM7600 HAT, Servo, optional ESP32 VIN.

## Benötigte Teile

- USB‑C Powerbank (≥18 W PD) + USB‑C ↔ USB‑C Kabel (e‑marked, 60 W)
- USB‑C PD‑Trigger (fix 5 V, bis 3 A)
- 2× WAGO 221‑415 (5‑polig) für +5 V und GND
- Silikonlitzen (0.5–1.0 mm²); falls der PD‑Trigger nur Lötpads hat, kurze Abgänge anlöten
- ESP32 DevKit, Servo (SG90/SG92R), Hall‑Sensor A3144; optional SIM7600 HAT A
- Optional: 1000 µF / 25 V (HAT), 330–470 µF / 25 V (Servo) + je 100 nF Keramik

## Schritt 1 – PD‑Trigger auf 5 V prüfen

1. Powerbank an den PD‑Trigger anschließen (USB‑C). 
2. 5.0 V am Ausgang (Vout/GND) per Multimeter prüfen oder Display/LEDs am Trigger beachten.
3. Kein Output? Anderes e‑marked Kabel testen; manche Powerbanks brauchen Last/Knopfdruck.

## Schritt 2 – WAGO‑Busse aufbauen

1. Zwei WAGO 221‑415 bereitlegen: eine für +5 V, eine für GND.
2. PD‑Trigger Vout (+) direkt in die +5‑V‑WAGO, PD‑Trigger GND (–) in die GND‑WAGO.
3. Leitungsquerschnitt: Hauptzufuhr ideal 0.75–1.0 mm². 
4. Zugprobe an allen Leitungen, Deckel ganz schließen.

## Schritt 3 – Verbraucher sternförmig anbinden

- SIM7600 HAT A: VCC → +5‑V‑WAGO, GND → GND‑WAGO. UART: TX→ESP32 RX2 (GPIO16), RX→ESP32 TX2 (GPIO17). Antennen anschließen.
- ESP32: Variante VIN → VIN an +5 V, GND an GND; oder USB‑Versorgung + gemeinsame Masse zum GND‑Bus.
- Servo: Rot → +5 V, Braun/Schwarz → GND, Signal → ESP32 GPIO 18. Achtung: nie an 3.3 V betreiben.
- Hall A3144: VCC → 3.3 V (ESP32), GND → GND, OUT → GPIO 19.

Tipp: Abgänge 0.5–0.75 mm²; Längen kurz halten.

## Schritt 4 – Optional Pufferkondensatoren

- 1000 µF/25 V Low‑ESR zwischen +5 V/GND nahe HAT; 330–470 µF/25 V nahe Servo. 
- Je 100 nF Keramik parallel, Polung bei Elkos beachten.

## Schritt 5 – Mechanik & Sicherheit

- PD‑Trigger und WAGOs sicher fixieren (Klebepad/Schrauben).
- Kabel so führen, dass der Servo nicht zerrt. 
- Vor Inbetriebnahme Polung prüfen (Rot = +5 V, Schwarz = GND).

## Erststart & Kurztest

- Powerbank einschalten → 5.0 V am Trigger prüfen.
- ESP32 Boot‑LED an? Seriellen Monitor 115200 Baud öffnen.

WiFi‑Variante:
1. `hardware/smart_parking_all_in_one.ino` flashen.
2. `BACKEND_BASE` auf LAN‑IP deines Rechners (Port 8000) stellen.
3. Hall betätigen → Statuswechsel im seriellen Monitor.

LTE‑Variante:
1. `hardware/smart_parking_sim7600_all_in_one.ino` flashen.
2. `APN=gprs.swisscom.ch`, `SERVER_HOST=https://<dein‑trycloudflare>.trycloudflare.com`, `USE_HTTPS=1`.
3. Health‑Ping erwartet `200`; Hall‑Event → POST am Backend sichtbar.

## Troubleshooting

- Servo‑Zucken/Resets: gemeinsame Masse prüfen, Querschnitt erhöhen, Pufferkondensatoren setzen.
- Keine 5 V: anderes USB‑C Kabel, Powerbank aktivieren.
- SIM‑Probleme: APN/Antennen/UART‑Pins checken.
- Backend: Tunnel‑Domain aktuell, `/health` liefert 200, CORS/Ports passend.

Viel Erfolg beim Aufbau – ohne Hohlstecker, mit maximal einfacher Verkabelung! 🚗
