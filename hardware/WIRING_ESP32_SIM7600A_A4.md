# Verdrahtung (A4) – ESP32 + SIM7600 HAT (A) + Servo + Hall

Dieses Blatt ist zum Ausdrucken (A4, randlos oder 100%). Es visualisiert die Versorgung über den vorhandenen 5‑V‑Regler aus deiner Einkaufsliste (Pololu S13V20F5) – kein zusätzliches Teil.

## Dateien
- WIRING_ESP32_SIM7600A_A4.svg – Vektorgrafik (für gestochen scharfen Druck)

## Stückliste (BOM)
- ESP32 DevKit (NodeMCU/WROOM‑32)
- SIM7600G‑H 4G LTE HAT (A) – UART‑Pins verfügbar
- SG92R Micro‑Servo
- Hall‑Sensor A3144 (oder M5Stack Hall Unit)
- 2× 18650 Li‑Ion (geschützt) + 2‑fach Halter
- Pololu S13V20F5 Step‑Up/Down 5 V / 2 A (aus deiner Liste, Pos. 7)
- Elkos: 470–1000 µF (HAT), 220–470 µF (Servo)
- Jumperkabel, optional Breadboard

## Verkabelungs‑Essenz
- 2×18650 → Pololu 5 V → 5V‑Bus
- 5V‑Bus versorgt SIM7600 HAT (A) und Servo direkt; ESP32 wahlweise via USB oder VIN
- GND überall gemeinsam
- UART: ESP32 GPIO17 (TX2) → HAT RXD; ESP32 GPIO16 (RX2) ← HAT TXD
- Servo Signal: ESP32 GPIO18
- Hall OUT: ESP32 GPIO19 (mit INPUT_PULLUP oder 10 kΩ nach 3V3)

## Druckhinweise
- Im Druckdialog „Tatsächliche Größe“/100% wählen (nicht „An Seite anpassen“)
- Papier: A4 Hochformat
- Optional randlos für maximalen Platz

## Hinweise zur Stromversorgung
- Pololu S13V20F5 reicht oft für Prototypen. Bei LTE‑Peaks ggf. auf 5 V / 3 A Buck upgraden.
- Elkos (optional, empfohlen): nahe am HAT (470–1000 µF) und am Servo (220–470 µF) setzen.
- Servo nie an 3V3 betreiben, immer 5 V. Masse immer gemeinsam.

Stand: 2025‑10‑13