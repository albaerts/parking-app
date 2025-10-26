# Smart Parking – Projektübersicht (DE)

Stand: 18.10.2025

Dieses Repository enthält eine vollständige Backup-Struktur der Smart‑Parking Anwendung:

- Backend (FastAPI) unter `backend/`
- Frontend (React/CRACO/Tailwind) unter `frontend/`
- Hardware/Firmware und Verdrahtung unter `hardware/`
- Tests und Hilfsskripte unter `tests/` und im Projektwurzelverzeichnis

## Schnellstart

### Backend lokal starten
1. In den Ordner `backend/` wechseln und eine virtuelle Umgebung anlegen.
2. Abhängigkeiten installieren und den Server starten.

Der Server läuft standardmäßig auf `http://127.0.0.1:8000`.

Gesundheitscheck: `GET /health` sollte `200 OK` liefern.

### Frontend lokal starten
1. In den Ordner `frontend/` wechseln.
2. Abhängigkeiten installieren und Dev‑Server starten.

Das Frontend ist typischerweise unter `http://localhost:3000` erreichbar.

Hinweis: Das Frontend ruft teils PHP‑artige Endpunkte (z. B. `/login.php`) auf. Im Backend existieren dafür kompatible Entwicklungs‑Routen.

## Öffentliche Erreichbarkeit (optional)

Für Tests mit Geräten (ESP32/LTE) kann das Backend via Cloudflare Quick Tunnel öffentlich gemacht werden. Siehe Dokumentation in den Projektdateien.

## Hardware/Firmware

- Verdrahtungs‑Übersicht: `hardware/WIRING_ESP32_SIM7600A_A4.md` (+ SVG)
- ESP32 WiFi All‑in‑One: `hardware/smart_parking_all_in_one.ino`
- ESP32 + SIM7600 All‑in‑One: `hardware/smart_parking_sim7600_all_in_one.ino`

## Weitere Dokumente

- Einkaufslisten (CH): `DIGITEC_BESTELLHILFE_ZUERICH.md`, `SMART_PARKING_EINKAUFSLISTE.md`
- Setup‑Guides und Troubleshooting: diverse `*.md` Dateien im Root
- Konversations‑Zusammenfassung: `CONVERSATION_EXPORT.md`
 - Aufbauanleitung Variante A (Powerbank + PD‑Trigger): `hardware/ASSEMBLY_QUICKSTART_VAR_A.md`
 - Aufbauanleitung Variante A – ohne DC‑Stecker: `hardware/ASSEMBLY_QUICKSTART_VAR_A_NO_DC.md`
 - End‑to‑End Testleitfaden: `hardware/END_TO_END_TEST.md`

## Lizenz/Urheberrecht

Interne Projektdokumentation (Backup). Nutzung gemäß interner Vereinbarungen. 
