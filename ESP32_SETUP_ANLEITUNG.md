# 🚀 ESP32 Prototyp mit deinem Account verbinden

## 📋 Was du hast
- ✅ ESP32 Dev Board
- ✅ SIM7600 Modem (nutzt aber WiFi für lokale Tests)
- ✅ Hall Sensor (Magnetsensor) für Fahrzeugerkennung
- ✅ Servo SG92R für Parkbügel
- ✅ Hardware-ID bereits zugewiesen: `PARK_DEVICE_001`
- ✅ Account: albert@gashis.ch (Owner)

## 📁 Dateien die ich erstellt habe

1. **ESP32_CONFIG_LOCAL.h** - Deine Konfigurationsdatei
2. **ESP32_SmartParking_Local.ino** - Vereinfachtes Arduino-Sketch für lokale Tests

## 🔧 Schritt 1: Konfiguration anpassen

### 1.1 Öffne `ESP32_CONFIG_LOCAL.h`

Passe diese Werte an:

```cpp
// WIFI - Ersetze mit deinen Daten
const char* WIFI_SSID = "DEIN_WIFI_NAME";
const char* WIFI_PASSWORD = "DEIN_WIFI_PASSWORT";

// SERVER - Finde deine Computer-IP
const char* LOCAL_API_BASE = "http://192.168.1.100:8000";
```

### 1.2 Finde deine Computer-IP

**macOS:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
```

Oder: System Preferences → Network → die IP steht dort

**Beispiel:** Wenn deine IP `192.168.1.145` ist:
```cpp
const char* LOCAL_API_BASE = "http://192.168.1.145:8000";
```

⚠️ **WICHTIG:** Nicht `localhost` verwenden! ESP32 braucht die echte IP!

## 🔌 Schritt 2: Hardware verbinden

### Pin-Belegung (laut Config):

| Komponente | ESP32 Pin | Beschreibung |
|------------|-----------|--------------|
| Hall Sensor | GPIO 32 | Signal-Pin (analogRead) |
| Servo SG92R | GPIO 25 | PWM-Signal |
| SIM7600 TX | GPIO 17 | (optional, noch nicht genutzt) |
| SIM7600 RX | GPIO 16 | (optional, noch nicht genutzt) |
| Status LED | GPIO 2 | Eingebaute LED |

### Verkabelung:

**Hall Sensor (A3144E oder ähnlich):**
```
VCC  → 3.3V (ESP32)
GND  → GND
OUT  → GPIO32
```

**Servo SG92R:**
```
Rot    → 5V (externe Power empfohlen!)
Braun  → GND
Orange → GPIO25
```

⚠️ **Servo-Power:** SG92R kann bis zu 500mA ziehen. Besser externe 5V-Quelle nutzen!

## 💻 Schritt 3: Arduino IDE vorbereiten

### 3.1 Bibliotheken installieren

Gehe zu: **Sketch → Include Library → Manage Libraries**

Installiere:
- ✅ `ESP32Servo` by Kevin Harrington
- ✅ `ArduinoJson` by Benoit Blanchon (v6 oder höher)
- ✅ `WiFi` (sollte mit ESP32 Board dabei sein)
- ✅ `HTTPClient` (sollte mit ESP32 Board dabei sein)

### 3.2 Board einstellen

**Tools → Board:** "ESP32 Dev Module"
**Tools → Upload Speed:** 115200
**Tools → Port:** Wähle deinen COM/USB Port

## 📤 Schritt 4: Hochladen

1. Öffne `ESP32_SmartParking_Local.ino` in Arduino IDE
2. Stelle sicher, dass `ESP32_CONFIG_LOCAL.h` im gleichen Ordner ist
3. Klicke auf **Upload** (→ Pfeil-Button)
4. Warte bis "Done uploading" erscheint

## 🖥️ Schritt 5: Serial Monitor öffnen

1. **Tools → Serial Monitor**
2. Stelle Baud-Rate auf **115200**
3. Du solltest sehen:

```
==================================
ESP32 Smart Parking Prototyp
==================================

1. WiFi verbinden...
Verbinde mit WiFi: DEIN_WIFI_NAME
....
✅ WiFi verbunden!
IP-Adresse: 192.168.1.XXX
Signal: -45 dBm

2. Hall-Sensor kalibrieren...
Kalibriere Hall-Sensor...
✅ Baseline: 2048

3. Test-Telemetrie senden...
📤 Sende Telemetrie:
   {"battery_level":3.7,"rssi":-45,"occupancy":"free"}
✅ Telemetrie gesendet

✅ Setup abgeschlossen!
==================================
Device-ID: PARK_DEVICE_001
Server: http://192.168.1.145:8000
==================================

✓ Keine neuen Commands
```

## 🧪 Schritt 6: In der Web-App testen

### 6.1 Backend & Frontend starten

**Terminal 1 - Backend:**
```bash
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235
source .venv-1/bin/activate
uvicorn backend.server_gashis:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend
npm start
```

### 6.2 In der Web-App

1. Gehe zu: http://localhost:3000
2. Login als: albert@gashis.ch
3. Klicke auf Tab: **"📡 Geräte"**
4. Du solltest sehen:
   - Hardware-ID: PARK_DEVICE_001
   - Parkplatz-ID: [deine zugewiesene ID]
   - Zuletzt gesehen: [gerade eben]
   - Belegung: Frei
   - Batterie: 3.70 V
   - RSSI: -45 dBm (oder dein aktueller Wert)

### 6.3 Commands testen

**Option A: In der Web-App (Sports Tab):**
1. Gehe zu Tab: **"🗺️ Parking Spots Map"**
2. Scroll runter zu "Owner Manual Hardware Controls"
3. Klicke: **"Raise Barrier"**

**Was passiert:**
- Web-App sendet Command an Backend
- ESP32 holt Command ab (beim nächsten Poll, max. 10 Sekunden)
- Im Serial Monitor siehst du:
  ```
  📥 1 Command(s) empfangen
    → Command #1: raise_barrier
  ⬆️  Hebe Bügel...
  ✅ Bügel oben
  ```
- Servo bewegt sich von 0° auf 90°

4. Klicke: **"Lower Barrier"**
- Servo geht zurück auf 0°

## 📊 Schritt 7: Realtime-Daten überprüfen

### Im Geräte-Tab aktualisieren

Alle 30 Sekunden sendet der ESP32 automatisch Telemetrie:

```
📤 Sende Telemetrie:
   {"battery_level":3.7,"rssi":-45,"occupancy":"free"}
✅ Telemetrie gesendet
```

Klicke auf **"Aktualisieren"** im Geräte-Tab → Daten werden aktualisiert!

### Belegung testen

1. Halte einen Magneten an den Hall-Sensor
2. Im Serial Monitor siehst du:
   ```
   🚗 Belegung geändert: BELEGT
   ```
3. Nach max. 30 Sekunden (beim nächsten Telemetrie-Send):
4. Im Geräte-Tab: **Belegung: Belegt** (rot)

## 🐛 Troubleshooting

### ❌ "WiFi-Verbindung fehlgeschlagen"
- Überprüfe SSID und Passwort in `ESP32_CONFIG_LOCAL.h`
- Ist 2.4GHz WiFi? ESP32 kann kein 5GHz

### ❌ "HTTP Fehler: -1" oder "Verbindungsfehler"
- Überprüfe Server-IP in `ESP32_CONFIG_LOCAL.h`
- Ist Backend gestartet? (uvicorn auf Port 8000)
- Firewall? Teste: `curl http://DEINE_IP:8000/`

### ❌ "404 Not Found"
- URL falsch? Sollte sein: `http://IP:8000` (ohne `/api` am Ende)
- Das Arduino-Sketch fügt `/hardware/...` automatisch hinzu

### ❌ "Keine Telemetrie im Geräte-Tab"
- Warte 30 Sekunden (Interval)
- Klicke "Aktualisieren"
- Schau im Serial Monitor: Wird "✅ Telemetrie gesendet" angezeigt?

### ❌ "Commands kommen nicht an"
- Warte 10 Sekunden (Poll-Interval)
- Schau im Serial Monitor: Wird "📥 Command empfangen" angezeigt?
- Im Backend: Sind Commands in der DB? 
  ```bash
  sqlite3 backend/parking.db "SELECT * FROM hardware_commands;"
  ```

### ❌ "Servo bewegt sich nicht"
- Externe 5V-Quelle angeschlossen?
- Pin korrekt? (GPIO25)
- Teste manuell im Arduino:
  ```cpp
  barrierServo.write(90);  // Sollte sich bewegen
  ```

## 📈 Nächste Schritte

### ✅ Was funktioniert jetzt:
- WiFi-Verbindung
- Commands empfangen (raise/lower barrier)
- Telemetrie senden (Batterie, Signal, Belegung)
- Hall-Sensor Belegungserkennung
- Servo-Steuerung
- Realtime-Anzeige in Web-App

### 🚀 Erweiterungen:
1. **SIM7600 für 4G/LTE** (ohne WiFi)
2. **Solarpanel & Batterie** (echte Batteriemessung)
3. **Deep Sleep** (Stromsparen)
4. **Magnetometer** (MMC5603 für präzisere Erkennung)
5. **HTTPS** (Verschlüsselte Kommunikation)

## 📚 Wichtige Dateien

```
ESP32_CONFIG_LOCAL.h              ← Deine Konfiguration
ESP32_SmartParking_Local.ino      ← Arduino-Sketch
HARDWARE_INTEGRATION_TEST.md      ← API-Dokumentation
Final_SmartParking_Firmware/      ← Original-Firmware (komplex)
```

## 🎯 Quick Commands

**Backend starten:**
```bash
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235
source .venv-1/bin/activate
uvicorn backend.server_gashis:app --reload --port 8000
```

**Frontend starten:**
```bash
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend
npm start
```

**Deine IP finden:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Telemetrie manuell testen:**
```bash
curl -X POST http://localhost:8000/api/hardware/PARK_DEVICE_001/telemetry \
  -H "Content-Type: application/json" \
  -d '{"battery_level":3.7,"rssi":-72,"occupancy":"free"}'
```

**Commands in DB ansehen:**
```bash
sqlite3 backend/parking.db "SELECT * FROM hardware_commands WHERE hardware_id='PARK_DEVICE_001';"
```

## ✅ Checkliste

- [ ] `ESP32_CONFIG_LOCAL.h` erstellt und angepasst
- [ ] WiFi SSID & Passwort eingetragen
- [ ] Computer-IP ermittelt und eingetragen
- [ ] Bibliotheken installiert (ESP32Servo, ArduinoJson)
- [ ] Hardware verbunden (Hall-Sensor, Servo)
- [ ] Sketch hochgeladen
- [ ] Serial Monitor geöffnet (115200 baud)
- [ ] Backend läuft (Port 8000)
- [ ] Frontend läuft (Port 3000)
- [ ] Device in Web-App zugewiesen
- [ ] Telemetrie im Geräte-Tab sichtbar
- [ ] Commands funktionieren (Raise/Lower Barrier)

Viel Erfolg! 🎉
