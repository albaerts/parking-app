# Smart Parking ESP32 + SIM7600E-H - Production Firmware

**Status:** ✅ Production Ready  
**Letzte Verifikation:** 16.11.2025  
**Device ID:** PARK_DEVICE_001  
**Server:** parking.gashis.ch (HTTPS)

## Hardware Requirements

- **Mikrocontroller:** ESP32-D0WDQ6 (oder kompatibel)
- **LTE Modem:** SIM7600E-H
- **Servo:** SG92R (oder kompatibel, 180°)
- **Magnetometer:** MMC5603 (I2C)
- **SIM Card:** Swisscom (oder kompatibel, kein PIN)

## Pin Configuration

```cpp
#define SIM_TX 26    // ESP32 TX → SIM7600 RXD
#define SIM_RX 27    // ESP32 RX → SIM7600 TXD
#define SERVO_PIN 14 // Servo Signal
#define I2C_SDA 21   // Magnetometer SDA
#define I2C_SCL 22   // Magnetometer SCL
#define STATUS_LED 2 // Built-in LED
```

**Wichtig:** SIM7600 muss mit 3.3V UART betrieben werden!

## Libraries

Über Arduino Library Manager installieren:

1. **TinyGSM** v0.12.0
   - Sketch → Include Library → Manage Libraries
   - Suche: "TinyGSM"
   - Version 0.12.0 installieren

2. **ArduinoJson** v7.4.2
   - Sketch → Include Library → Manage Libraries
   - Suche: "ArduinoJson"
   - Version 7.4.2 installieren

3. **ESP32Servo** (neueste Version)
   - Sketch → Include Library → Manage Libraries
   - Suche: "ESP32Servo"

4. **Wire** (Built-in, I2C Library)

## Configuration

### 1. Network Settings

```cpp
const char* APN = "gprs.swisscom.ch";  // Swisscom APN
```

Für andere Provider:
- **Sunrise:** `internet.sunrise.ch`
- **Salt:** `internet.salt.ch`

### 2. Server Settings

```cpp
const char* DEVICE_ID = "PARK_DEVICE_001";
const char* API_HOST = "parking.gashis.ch";
const char* API_BASE = "/api";
const int API_PORT = 443;  // HTTPS
```

### 3. Timing

```cpp
const unsigned long HEARTBEAT_INTERVAL = 30000;      // 30s Telemetrie
const unsigned long COMMAND_POLL_INTERVAL = 10000;   // 10s Command Poll
```

## Upload Instructions

### Via arduino-cli

```bash
# Board installieren (falls noch nicht vorhanden)
arduino-cli core install esp32:esp32

# Kompilieren
arduino-cli compile --fqbn esp32:esp32:esp32 parking_tinygsm.ino

# Upload (Port anpassen!)
arduino-cli upload -p /dev/cu.usbserial-0001 --fqbn esp32:esp32:esp32 parking_tinygsm
```

### Via Arduino IDE

1. **Board Manager:**
   - Tools → Board → ESP32 → ESP32 Dev Module

2. **Port Selection:**
   - Tools → Port → `/dev/cu.usbserial-XXXX` (macOS)
   - Tools → Port → `COMX` (Windows)

3. **Upload Settings:**
   - Upload Speed: 921600
   - Flash Frequency: 80MHz
   - Partition Scheme: Default

4. **Upload:**
   - Sketch → Upload (⌘U / Ctrl+U)

## Serial Monitor

```bash
# Mit screen (macOS/Linux)
screen /dev/cu.usbserial-0001 115200

# Beenden: Ctrl+A, dann K, dann Y
```

### Expected Output

```
==================================
Smart Parking + SIM7600 (TinyGSM)
==================================
✅ MMC5603 detected
Baseline: X=31477, Y=-32359, Z=29233
Init Modem...
✅ Modem responsive
Modem: SIM7600E-H
Warte auf Netzwerk...
✅ Im Netz registriert
Signal: 25
Verbinde GPRS...
APN: gprs.swisscom.ch
✅ GPRS verbunden
IP: 10.58.95.236
📡 POST https://parking.gashis.ch/api/hardware/PARK_DEVICE_001/telemetry
⏳ Waiting for HTTP response...
HTTP Response: +HTTPACTION: 1,200,93
Status Code: 200
✅ HTTPS Success
✅ Setup abgeschlossen
```

## Troubleshooting

### Modem antwortet nicht
- **Check:** Verkabelung SIM_TX/RX (GPIO 26/27)
- **Check:** SIM7600 Power (muss eingeschaltet sein)
- **Fix:** Hardware Reset am SIM7600 Modul

### GPRS Connection Failed
- **Check:** SIM Card eingelegt und erkannt
- **Check:** APN korrekt (`gprs.swisscom.ch` für Swisscom)
- **Check:** Signal Strength (min. 10)
- **Fix:** Andere APN probieren oder SIM Card tauschen

### HTTPS Request Failed
- **Check:** Server erreichbar (ping parking.gashis.ch)
- **Check:** Device ID in Datenbank registriert
- **Check:** AT+HTTPACTION Response im Serial Monitor
- **Known Issue:** Bei Status Code 200 aber "Failed" → Code bereits gefixt in v358

### Magnetometer nicht erkannt
- **Check:** I2C Verkabelung (SDA=21, SCL=22)
- **Check:** I2C Address (0x30 für MMC5603)
- **Fix:** `i2cdetect` auf ESP32 ausführen

## Performance

- **Compile Size:** 332 KB (25% Flash)
- **RAM Usage:** ~40 KB
- **Boot Time:** ~10 Sekunden
- **HTTPS Request:** ~2-3 Sekunden
- **Battery Life:** ~2 Wochen (mit 5000mAh bei 30s Heartbeat)

## API Endpoints

### POST Telemetry
```
POST /api/hardware/PARK_DEVICE_001/telemetry
Content-Type: application/json

{
  "battery_level": 3.7,
  "rssi": 25,
  "occupancy": "free",
  "last_mag": {"x": 31477, "y": -32359, "z": 29233}
}
```

### GET Commands
```
GET /api/hardware/PARK_DEVICE_001/commands

Response:
[
  {"id": 1, "type": "raise_barrier"},
  {"id": 2, "type": "lower_barrier"}
]
```

## Production Checklist

- [x] Libraries installiert (TinyGSM, ArduinoJson, ESP32Servo)
- [x] Pin Configuration verifiziert
- [x] APN korrekt (gprs.swisscom.ch)
- [x] Device ID registriert (PARK_DEVICE_001 → Parking Spot 19)
- [x] HTTPS funktioniert (Status Code 200)
- [x] Magnetometer kalibriert
- [x] Servo funktioniert
- [x] Telemetrie empfangen (Server DB updates)

## License

MIT License - Smart Parking System 2025
