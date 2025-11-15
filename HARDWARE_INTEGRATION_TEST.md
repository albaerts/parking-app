# Hardware Integration - Test & Erklärung

## 🔌 Dein Setup

Du hast erfolgreich verbunden:
- **Hardware-ID**: `PARK_DEVICE_001` (oder deine gewählte ID)
- **Parkplatz**: Zugewiesen über "Device zuweisen" im Owner Dashboard
- **Owner**: albert@gashis.ch

## 📡 So funktioniert die Kommunikation

### 1. Befehle senden (Raise/Lower Barrier)

**Von der Web-App aus:**
1. Du klickst auf "Raise Barrier" oder "Lower Barrier"
2. Frontend sendet Command an: `POST /api/hardware/PARK_DEVICE_001/commands/queue`
3. Backend speichert den Befehl in der `hardware_commands` Tabelle mit status='queued'
4. Du siehst die Meldung: "Command queued: raise_barrier"

**✅ Dieser Teil funktioniert jetzt!** (Gerade gefixt - JWT-Token wird nun akzeptiert)

### 2. Befehle abholen (Dein ESP32/Arduino muss das tun)

**Dein Gerät muss regelmäßig pollen:**
```cpp
// Im Arduino/ESP32 Code - alle 5-10 Sekunden
void pollCommands() {
  HTTPClient http;
  String url = "http://localhost:8000/api/hardware/PARK_DEVICE_001/commands";
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    // Parse JSON und führe Befehle aus
    // { "commands": [{"id": 1, "command": "raise_barrier", "parameters": {}}] }
  }
  http.end();
}
```

**Das Backend macht dann:**
- Liefert alle Commands mit status='queued'
- Markiert sie als status='sent'
- Dein Gerät führt sie aus (z.B. Servo bewegen)

### 3. Telemetrie senden (Realtime-Daten)

**Dein ESP32/Arduino muss Daten senden:**
```cpp
// Alle 30 Sekunden oder bei Änderungen
void sendTelemetry() {
  HTTPClient http;
  String url = "http://localhost:8000/api/hardware/PARK_DEVICE_001/telemetry";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  String json = "{";
  json += "\"battery_level\": 3.7,";  // Batteriespannung in Volt
  json += "\"rssi\": -65,";            // WiFi Signal in dBm
  json += "\"occupancy\": \"free\",";  // "free" oder "occupied"
  json += "\"last_mag\": {\"x\": 0.1, \"y\": 0.2, \"z\": 0.9}";  // Magnetometer
  json += "}";
  
  http.POST(json);
  http.end();
}
```

**Das Backend macht dann:**
- Speichert die Daten in `hardware_devices` Tabelle
- Updated die Spalten: `last_heartbeat`, `battery_level`, `rssi`, `occupancy`, `last_mag`

**Du siehst die Daten dann:**
- Im Tab "📡 Geräte" im Owner Dashboard
- Unter "Zuletzt gesehen", "Belegung", "Batterie", "RSSI"

## 🧪 Testen ohne echtes Gerät

Du kannst die API direkt testen:

### Test 1: Telemetrie senden
```bash
curl -X POST http://localhost:8000/api/hardware/PARK_DEVICE_001/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "battery_level": 3.7,
    "rssi": -72,
    "occupancy": "free",
    "timestamp": "2025-11-10T14:30:00"
  }'
```

### Test 2: Commands abholen
```bash
curl http://localhost:8000/api/hardware/PARK_DEVICE_001/commands
```

### Test 3: Command senden (mit deinem Token)
```bash
# Zuerst Token aus localStorage holen (in Browser Console):
# localStorage.getItem('token')

curl -X POST http://localhost:8000/api/hardware/PARK_DEVICE_001/commands/queue \
  -H "Authorization: Bearer DEIN_TOKEN_HIER" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "raise_barrier",
    "parameters": {}
  }'
```

## 🎯 Nächste Schritte für dein Gerät

1. **ESP32/Arduino Code anpassen:**
   - WiFi-Verbindung herstellen
   - API-Endpoint auf `http://localhost:8000` (oder deine Server-IP) setzen
   - Polling-Loop für Commands einbauen (alle 5-10 Sekunden)
   - Telemetrie-Sending einbauen (alle 30 Sekunden)

2. **Basis-Firmware verwenden:**
   - Schau dir an: `Final_SmartParking_Firmware/Final_SmartParking_Firmware.ino`
   - Dort sind bereits `pollCommands()` und `sendTelemetry()` Funktionen

3. **Testen:**
   - Starte dein Gerät
   - In der Web-App: Klicke "Raise Barrier"
   - Dein Gerät sollte beim nächsten Poll den Befehl abholen
   - Nach 30 Sekunden solltest du Telemetrie-Daten im "📡 Geräte" Tab sehen

## 🐛 Troubleshooting

### "Raise/Lower Barrier funktioniert nicht"
- ✅ **GELÖST**: JWT-Token wird jetzt akzeptiert
- Überprüfe: Öffne Browser Console (F12) - siehst du Fehler?
- Teste: Klicke auf "Befehle anzeigen" im Geräte-Tab - sind Commands in der Queue?

### "Keine Realtime-Daten"
- ❌ **Dein Gerät sendet noch keine Daten**
- Lösung: ESP32/Arduino muss aktiv sein und Telemetrie senden
- Test: Sende manuell via curl (siehe oben), dann "Aktualisieren" im Geräte-Tab

### "Gerät nicht verbunden"
- Überprüfe: WiFi-Verbindung auf dem ESP32/Arduino
- Überprüfe: Richtige Server-IP im Code (nicht localhost, sondern deine Computer-IP)
- Test: Ping von ESP32 zum Server

## 📊 Datenbank-Struktur

### hardware_devices Tabelle
```sql
CREATE TABLE hardware_devices (
    id INTEGER PRIMARY KEY,
    hardware_id TEXT UNIQUE,
    owner_email TEXT,
    parking_spot_id INTEGER,
    created_at TEXT,
    last_heartbeat TEXT,      -- Letzte Telemetrie
    battery_level REAL,        -- Batteriespannung
    rssi INTEGER,              -- WiFi Signal
    occupancy TEXT,            -- "free" / "occupied"
    last_mag TEXT              -- JSON: {x, y, z}
);
```

### hardware_commands Tabelle
```sql
CREATE TABLE hardware_commands (
    id INTEGER PRIMARY KEY,
    hardware_id TEXT,
    command TEXT,              -- "raise_barrier", "lower_barrier"
    parameters TEXT,           -- JSON
    status TEXT DEFAULT 'queued',  -- 'queued' -> 'sent' -> 'completed'
    created_at TEXT,
    issued_by TEXT             -- Wer hat den Befehl gesendet
);
```

## ✅ Status

- ✅ Device-Zuweisung funktioniert
- ✅ Commands können gesendet werden (raise/lower barrier)
- ✅ Backend speichert Commands in DB
- ✅ Geräte-Tab ist sichtbar für Owner
- ⏳ ESP32/Arduino muss noch aktiv sein (Commands abholen)
- ⏳ ESP32/Arduino muss noch Telemetrie senden
