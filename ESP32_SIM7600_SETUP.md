# 🚀 ESP32 + SIM7600 Setup - Mit LTE/4G

## 📱 Hardware-Setup

### Was du hast:
- ✅ ESP32 Dev Board
- ✅ SIM7600E Modem (LTE/4G)
- ✅ SIM-Karte mit Daten-Abo
- ✅ Hall Sensor (GPIO32)
- ✅ Servo SG92R (GPIO25)

### Pin-Verbindungen:

```
SIM7600 → ESP32:
  TX    → GPIO16 (RX2)
  RX    → GPIO17 (TX2)
  PWR   → GPIO4
  VCC   → 5V
  GND   → GND

Hall Sensor → ESP32:
  VCC   → 3.3V
  GND   → GND
  OUT   → GPIO32

Servo SG92R → ESP32:
  Rot   → 5V (externe Power!)
  Braun → GND
  Orange→ GPIO25
```

## 📋 SIM-Karte Einstellungen

### Schweizer Provider:

**Swisscom:**
- APN: `gprs.swisscom.ch`
- Im Code (Zeile 202): `AT+CGDCONT=1,"IP","gprs.swisscom.ch"`

**Salt / Sunrise:**
- APN: `internet`
- Im Code (Zeile 203): `AT+CGDCONT=1,"IP","internet"`

### Wichtig:
- ✅ SIM-Karte hat Daten-Abo aktiviert
- ✅ PIN-Code deaktiviert (oder im Code eingeben)
- ✅ Roaming aktiviert (falls nötig)

## 🔧 Software-Setup

### 1. Datei öffnen

Arduino IDE:
```
Öffne: ESP32_SmartParking_SIM7600.ino
```

Die Config-Datei `ESP32_CONFIG_LOCAL.h` sollte automatisch als Tab erscheinen.

### 2. Config anpassen

Öffne `ESP32_CONFIG_LOCAL.h`:

```cpp
// Device-ID (bereits zugewiesen in Web-App)
const char* DEVICE_ID = "PARK_DEVICE_001";

// Server (Produktions-Server)
const char* PRODUCTION_API_BASE = "https://api.gashis.ch";

// Hardware Pins (schon richtig konfiguriert)
#define HALL_SENSOR_PIN 32
#define SERVO_PIN 25
#define SIM7600_RX 16
#define SIM7600_TX 17
#define SIM7600_PWR 4
```

### 3. APN anpassen (wenn nötig)

In `ESP32_SmartParking_SIM7600.ino`, Zeile ~202:

**Für Swisscom (Standard):**
```cpp
sendATCommand("AT+CGDCONT=1,\"IP\",\"gprs.swisscom.ch\"");
```

**Für Salt/Sunrise:**
```cpp
sendATCommand("AT+CGDCONT=1,\"IP\",\"internet\"");
```

### 4. Hochladen

Arduino IDE:
- **Board:** ESP32 Dev Module
- **Upload Speed:** 115200
- **Port:** Dein ESP32 USB-Port
- **Upload!**

## 📺 Serial Monitor

Nach dem Upload:

1. **Tools → Serial Monitor**
2. **Baud-Rate: 115200**

Du solltest sehen:

```
==================================
ESP32 Smart Parking - SIM7600
==================================

1. SIM7600 Modem initialisieren...
Power on Modem...
AT> AT
OK
✅ Modem antwortet

Modem Info:
AT> ATI
Manufacturer: SIMCOM
Model: SIM7600E
IMEI: 867123456789012

2. Mit Mobilfunknetz verbinden...
Warte auf Netzwerk-Registrierung...
...
✅ Im Netz registriert
Signal: 25/31

3. GPRS/LTE aktivieren...
Aktiviere GPRS/LTE...
AT> AT+CGDCONT=1,"IP","gprs.swisscom.ch"
OK
AT> AT+CGACT=1,1
OK
✅ GPRS verbunden
+CGPADDR: 1,"10.123.45.67"

4. Hall-Sensor kalibrieren...
Kalibriere Hall-Sensor...
✅ Baseline: 2048

5. Test-Telemetrie senden...
📤 Sende Telemetrie:
   {"battery_level":3.70,"rssi":25,"occupancy":"free","last_mag":{"x":0,"y":0,"z":0}}
HTTP POST...
✅ Telemetrie gesendet

✅ Setup abgeschlossen!
==================================
Device-ID: PARK_DEVICE_001
Server: https://api.gashis.ch
==================================
```

## 🌐 Server-Verbindung

### Lokale Tests (Development):

Dein Backend läuft auf `localhost:8000` - **das geht nicht** mit SIM7600!

**Lösung: ngrok verwenden**

```bash
# Terminal 1: Backend starten
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235
source .venv-1/bin/activate
uvicorn backend.server_gashis:app --reload --port 8000

# Terminal 2: ngrok starten
ngrok http 8000
```

ngrok gibt dir eine öffentliche URL:
```
Forwarding: https://abc123.ngrok.io → http://localhost:8000
```

Dann in `ESP32_CONFIG_LOCAL.h`:
```cpp
const char* PRODUCTION_API_BASE = "https://abc123.ngrok.io";
```

### Produktion:

Verwende `https://api.gashis.ch` (wenn deployed).

## 🧪 Testing

### 1. Modem-Test

Im Serial Monitor siehst du:
- ✅ Modem antwortet
- ✅ Im Netz registriert
- ✅ GPRS verbunden
- ✅ IP-Adresse erhalten

### 2. Telemetrie-Test

Alle 30 Sekunden:
```
📤 Sende Telemetrie:
   {"battery_level":3.70,"rssi":25,"occupancy":"free"}
✅ Telemetrie gesendet
```

In der Web-App (Tab "📡 Geräte"):
- Zuletzt gesehen: [gerade eben]
- Belegung: Frei
- RSSI: 25 (CSQ Signal Quality)

### 3. Commands-Test

Alle 10 Sekunden:
```
📥 Hole Commands...
  → raise_barrier
⬆️  Hebe Bügel...
✅ Bügel oben
```

## 🐛 Troubleshooting

### ❌ "Modem antwortet nicht"

**Check:**
- SIM7600 Power LED leuchtet?
- Verkabelung: TX↔RX richtig gekreuzt?
- Baud-Rate: 115200?

**Fix:**
```cpp
// In Code, Zeile 148-155
digitalWrite(SIM7600_PWR, LOW);
delay(2000);  // Länger warten
digitalWrite(SIM7600_PWR, HIGH);
delay(15000);  // Mehr Zeit für Boot
```

### ❌ "Netzwerk-Registrierung fehlgeschlagen"

**Check:**
- SIM-Karte eingelegt?
- SIM-Karte aktiviert (Daten-Abo)?
- PIN deaktiviert?
- Antenne angeschlossen?

**Fix PIN:**
```cpp
// Nach initModem(), Zeile ~176 hinzufügen:
sendATCommand("AT+CPIN=\"1234\"");  // Deine PIN
delay(5000);
```

### ❌ "GPRS-Verbindung fehlgeschlagen"

**Check:**
- APN korrekt? (Swisscom: gprs.swisscom.ch)
- Daten-Roaming aktiviert?
- Signal gut genug? (CSQ > 10)

**Fix APN:**
```cpp
// Zeile 202 ändern:
sendATCommand("AT+CGDCONT=1,\"IP\",\"DEIN_APN\"");
```

### ❌ "HTTP Fehler"

**Check:**
- Server erreichbar? (curl https://api.gashis.ch)
- GPRS verbunden?
- URL korrekt?

**Debug:**
```cpp
// Zeile ~245, mehr Logging:
Serial.println("Full Response:");
Serial.println(response);
```

### ❌ "Keine Telemetrie in Web-App"

**Check:**
- Backend läuft?
- Richtige URL in Config?
- Serial Monitor zeigt "✅ Telemetrie gesendet"?

**Test manuell:**
```bash
curl -X POST https://api.gashis.ch/api/hardware/PARK_DEVICE_001/telemetry \
  -H "Content-Type: application/json" \
  -d '{"battery_level":3.7,"rssi":25,"occupancy":"free"}'
```

## ⚡ Stromverbrauch

### Idle (connected):
- ESP32: ~80mA
- SIM7600: ~100-300mA (je nach Signal)
- **Total: ~200-400mA**

### Sleep Mode (später):
- Deep Sleep + SIM7600 Sleep: ~10mA
- Wake up alle 5 Min für 30s
- **Batterie-Laufzeit: Wochen/Monate**

## 🚀 Vorteile SIM7600 vs WiFi

### ✅ Vorteile:
- Überall einsetzbar (kein WiFi nötig)
- Robust (Mobilfunk stabiler als WiFi)
- Batteriebetrieb möglich
- Echtes IoT-Device

### ⚠️ Nachteile:
- Höherer Stromverbrauch
- SIM-Karte Kosten (CHF 5-10/Monat)
- Langsamere HTTP-Requests
- Komplexere Fehlerbehandlung

## 📊 Datenverbrauch

**Pro Tag:**
- Telemetrie (30s): ~50 Bytes × 2880 = ~140 KB
- Commands Poll (10s): ~100 Bytes × 8640 = ~860 KB
- **Total: ~1 MB/Tag**

**Pro Monat:**
- ~30 MB

➡️ **Empfehlung:** 100 MB Daten-Abo genügt!

## ✅ Checkliste

- [ ] ESP32 + SIM7600 verkabelt
- [ ] SIM-Karte eingelegt (mit Daten-Abo)
- [ ] PIN deaktiviert
- [ ] APN im Code angepasst
- [ ] Device-ID korrekt (PARK_DEVICE_001)
- [ ] Server-URL korrekt (api.gashis.ch oder ngrok)
- [ ] Sketch hochgeladen
- [ ] Serial Monitor zeigt "GPRS verbunden"
- [ ] Telemetrie im Geräte-Tab sichtbar
- [ ] Commands funktionieren

## 🎉 Erfolg!

Wenn alles läuft:
- ✅ LED leuchtet
- ✅ Serial Monitor zeigt "GPRS verbunden"
- ✅ Telemetrie wird alle 30s gesendet
- ✅ Commands werden alle 10s abgeholt
- ✅ Web-App zeigt Realtime-Daten
- ✅ Servo reagiert auf Commands

**→ Dein ESP32 ist jetzt ein echtes LTE-IoT-Device! 🚀📱**
