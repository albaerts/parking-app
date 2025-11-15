# 🎯 ESP32 Quick Reference - Dein Prototyp

## 📌 Hardware-Info

**Device-ID:** `PARK_DEVICE_001`  
**Owner:** albert@gashis.ch  
**Hardware:**
- ESP32 Dev Board
- SIM7600 Modem (nutzt WiFi)
- Hall Sensor (GPIO32)
- Servo SG92R (GPIO25)

## 🔌 Pin-Belegung

```
Hall Sensor:  GPIO 32 (analogRead)
Servo SG92R:  GPIO 25 (PWM)
Status LED:   GPIO 2  (eingebaut)
SIM7600 TX:   GPIO 17 (optional)
SIM7600 RX:   GPIO 16 (optional)
```

## 📡 API-Endpoints

### Commands abholen (ESP32 → Backend)
```
GET http://DEINE_IP:8000/api/hardware/PARK_DEVICE_001/commands
```

### Telemetrie senden (ESP32 → Backend)
```
POST http://DEINE_IP:8000/api/hardware/PARK_DEVICE_001/telemetry
Content-Type: application/json

{
  "battery_level": 3.7,
  "rssi": -55,
  "occupancy": "free",
  "last_mag": {"x": 0, "y": 0, "z": 0}
}
```

## 🚀 Quick Start

### 1. Deine IP finden
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### 2. Config anpassen
Öffne `ESP32_CONFIG_LOCAL.h` und ersetze:
```cpp
const char* WIFI_SSID = "DEIN_WIFI";
const char* WIFI_PASSWORD = "DEIN_PASSWORT";
const char* LOCAL_API_BASE = "http://192.168.1.XXX:8000";
```

### 3. Arduino IDE
- Öffne `ESP32_SmartParking_Local.ino`
- Board: ESP32 Dev Module
- Upload Speed: 115200
- Upload!

### 4. Serial Monitor (115200 baud)
```
✅ WiFi verbunden!
✅ Telemetrie gesendet
✓ Keine neuen Commands
```

## 🧪 Testen

### Backend & Frontend starten
```bash
# Terminal 1 - Backend
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235
source .venv-1/bin/activate
uvicorn backend.server_gashis:app --reload --port 8000

# Terminal 2 - Frontend
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend
npm start

# Terminal 3 - Connection Test
python3 test_esp32_connection.py
```

### In der Web-App
1. http://localhost:3000
2. Login: albert@gashis.ch
3. Tab: **📡 Geräte**
4. Siehst du PARK_DEVICE_001? ✅

### Commands testen
1. Tab: **🗺️ Parking Spots Map**
2. Scroll runter zu "Owner Manual Hardware Controls"
3. Klick: **Raise Barrier**
4. Im Serial Monitor:
   ```
   📥 1 Command(s) empfangen
     → Command #1: raise_barrier
   ⬆️  Hebe Bügel...
   ✅ Bügel oben
   ```

## 📊 Timing

- **Commands Poll:** alle 10 Sekunden
- **Telemetrie Send:** alle 30 Sekunden
- **WiFi Reconnect:** automatisch bei Verlust

## 🐛 Troubleshooting

| Problem | Lösung |
|---------|--------|
| WiFi-Fehler | Überprüfe SSID/Passwort, 2.4GHz? |
| HTTP -1 | Server-IP falsch oder Backend nicht gestartet |
| 404 Not Found | API_BASE sollte `http://IP:8000` sein (ohne `/api`) |
| Keine Telemetrie | Warte 30s, klick "Aktualisieren" im Geräte-Tab |
| Commands kommen nicht | Warte 10s, prüf Serial Monitor |
| Servo bewegt sich nicht | Externe 5V-Quelle? Pin GPIO25? |

## 🎛️ Kalibrierung

### Hall-Sensor
```cpp
const bool AUTO_CALIBRATE = true;  // Automatisch beim Start
```

Beim Hochfahren:
1. Kein Auto auf Platz haben
2. ESP32 startet
3. Kalibriert 2 Sekunden
4. Baseline gespeichert

### Servo
```cpp
const int SERVO_POS_DOWN = 0;   // Bügel unten
const int SERVO_POS_UP = 90;    // Bügel oben
```

Anpassen falls:
- Bügel nicht ganz unten/oben
- Montage anders orientiert

## 📱 Verfügbare Commands

| Command | Beschreibung |
|---------|--------------|
| `raise_barrier` | Hebt Parkbügel (90°) |
| `lower_barrier` | Senkt Parkbügel (0°) |
| `reset` | Neustart ESP32 |

## 💾 Dateien

```
ESP32_CONFIG_LOCAL.h           ← Deine Config (WiFi, IP)
ESP32_SmartParking_Local.ino   ← Arduino-Sketch
ESP32_SETUP_ANLEITUNG.md       ← Ausführliche Anleitung
test_esp32_connection.py       ← Test-Script
```

## ✅ Checkliste

- [ ] Config erstellt (`ESP32_CONFIG_LOCAL.h`)
- [ ] WiFi eingetragen
- [ ] IP eingetragen (nicht localhost!)
- [ ] Bibliotheken installiert (ESP32Servo, ArduinoJson)
- [ ] Hardware verbunden
- [ ] Sketch hochgeladen
- [ ] Serial Monitor offen (115200)
- [ ] Backend läuft (Port 8000)
- [ ] Frontend läuft (Port 3000)
- [ ] Device zugewiesen in Web-App
- [ ] Test-Script ausgeführt (`python3 test_esp32_connection.py`)
- [ ] Telemetrie sichtbar im Geräte-Tab
- [ ] Commands funktionieren

## 🎉 Erfolgstest

Wenn alles funktioniert:
1. ✅ Grüne LED leuchtet (GPIO2)
2. ✅ Serial Monitor zeigt keine Fehler
3. ✅ Geräte-Tab zeigt aktuelle Daten
4. ✅ Raise Barrier → Servo bewegt sich
5. ✅ Magnet an Hall-Sensor → Belegung ändert sich

**→ Prototyp läuft! 🚀**
