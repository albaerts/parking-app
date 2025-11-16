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

## Produktionsserver

Das Backend läuft auf dem eigenen Server unter `https://parking.gashis.ch/api`.

## Hardware/Firmware

- Verdrahtungs‑Übersicht: `hardware/WIRING_ESP32_SIM7600A_A4.md` (+ SVG)
- ESP32 WiFi All‑in‑One: `hardware/smart_parking_all_in_one.ino`
- ESP32 + SIM7600 All‑in‑One: `hardware/smart_parking_sim7600_all_in_one.ino`

## Weitere Dokumente

 - Aufbauanleitung Variante A (Powerbank + PD‑Trigger): `hardware/ASSEMBLY_QUICKSTART_VAR_A.md`
 - Aufbauanleitung Variante A – ohne DC‑Stecker: `hardware/ASSEMBLY_QUICKSTART_VAR_A_NO_DC.md`
 - End‑to‑End Testleitfaden: `hardware/END_TO_END_TEST.md`

## Lizenz/Urheberrecht

### /api/autocomplete

Kostenloser zusammengesetzter Autocomplete-Endpunkt (Photon + Nominatim) über das Backend.

Query Parameter:
- `q` (string, erforderlich): Suchtext ab 1 Zeichen.
- `limit` (int, optional, Standard 12, max 15): Begrenzung der Ergebnisanzahl.
- `countrycodes` (string, optional, Standard `ch,de,at`): Komma-separierte Länder für Nominatim Bias.
- `lat`, `lon` (float, optional): Nutzerposition zur leichten Ergebnis-Gewichtung.

Antwort (JSON Array von Objekten):
```
[
	{
		"id": "osm_123456",          // eindeutige ID (Quelle + place_id oder Photon-ID)
		"source": "osm" | "photon",   // Datenquelle
		"primary": "Titel",            // Hauptanzeige (Name / Straße / Ort)
		"secondary": "PLZ Ort",        // Zusatzinfos kompakt
		"address": "Vollständige Adresse", 
		"lat": 47.3769,
		"lng": 8.5417
	}
]
```

Eigenschaften:
- Kombiniert parallel beide Provider und entfernt Dubletten (`primary` + `secondary`).
- Fallback: Falls keine Treffer, zweiter Durchlauf mit weiterem Nominatim-Scope.
- Caching: 5 Minuten pro Suchkombination (inkl. Koordinaten Bias).
- Rate Limit: 30 Requests / 60 Sekunden pro IP (429 bei Überschreitung).
- Keine externen API Keys notwendig (rein Open Data).

Verwendung im Frontend: Die Komponente `AddressAutocomplete` ruft diesen Endpunkt mit Axios auf (`GET /api/autocomplete`). Bei Auswahl eines Eintrags werden Adresse und Koordinaten ins Formular übernommen.


Interne Projektdokumentation (Backup). Nutzung gemäß interner Vereinbarungen. 
