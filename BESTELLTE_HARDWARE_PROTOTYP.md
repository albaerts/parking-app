# 📦 BESTELLTE HARDWARE - SMART PARKING PROTOTYP
## Finale Komponenten-Liste & Projektplanung

*Stand: 10. August 2025*  
*Status: Hardware bestellt - bereit für Entwicklung*

---

## 🛒 **BESTELLTE KOMPONENTEN**

### **🔧 ELEKTRONIK & STEUERUNG**
| Komponente | Anzahl | Funktion | Status |
|------------|--------|-----------|---------|
| **ESP32 Dev Board** (NodeMCU/WROOM-32) | 1× | Hauptsteuerung, WiFi, Bluetooth | ✅ Bestellt |
| **SIM7600G-H 4G LTE Modul** (HAT B) | 1× | Mobilfunk & GPS Tracking | ✅ Bestellt |
| **SG92R Micro Servo** | 1× | Parkbügel Hebemechanismus | ✅ Bestellt |
| **Hall-Sensor A3144** | 1× | Fahrzeugerkennung (magnetisch) | ✅ Bestellt |

### **🔌 STROMVERSORGUNG**
| Komponente | Anzahl | Funktion | Status |
|------------|--------|-----------|---------|
| **18650 Li-Ion Akkus** (geschützt) | 2× | Hauptenergiequelle (7.4V) | ✅ Bestellt |
| **18650 Batteriehalter** (2×) | 1× | Sichere Akku-Halterung | ✅ Bestellt |
| **Pololu S13V20F5 Step-Up/Down** | 1× | Stabile 5V Versorgung (2A) | ✅ Bestellt |

### **🔗 VERKABELUNG & PROTOTYPING**
| Komponente | Anzahl | Funktion | Status |
|------------|--------|-----------|---------|
| **40-Pin Dupont Jumper Set** | 1× | Flexible Verbindungskabel | ✅ Bestellt |
| **Breadboard** (400 Punkte) | 1× | Prototyping & Tests | ✅ Bestellt |

### **🧱 MECHANIK & MONTAGE**
| Komponente | Anzahl | Funktion | Status |
|------------|--------|-----------|---------|
| **Acryl-/Prototypenplatte** | 1× | Stabile Montagebasis | ✅ Bestellt |
| **M3 Nylon Abstandshalter Set** | 1× | Professionelle Befestigung | ✅ Bestellt |

---

## 🎯 **SYSTEM-ARCHITEKTUR**

### **Hauptfunktionen:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ESP32 MCU     │◄──►│  SIM7600G-H     │◄──►│   Cloud API     │
│   (Steuerung)   │    │  (4G + GPS)     │    │ (gashis.ch)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Hall Sensor   │    │   SG92R Servo   │
│ (Fahrzeug-ID)   │    │  (Parkbügel)    │
└─────────────────┘    └─────────────────┘
```

### **Betriebsmodi:**
1. **FREI**: Grün, Bügel unten, wartet auf Fahrzeug
2. **BESETZT**: Rot, Bügel oben, Fahrzeug erkannt
3. **RESERVIERT**: Blau, Bügel oben, App-Reservierung aktiv
4. **WARTUNG**: Gelb, manueller Modus

---

## 💡 **TECHNISCHE SPEZIFIKATIONEN**

### **ESP32 Capabilities:**
- **CPU**: Dual-core 240 MHz
- **RAM**: 520 KB SRAM
- **Flash**: 4 MB (programmierbar)
- **WiFi**: 802.11 b/g/n
- **Bluetooth**: Classic + BLE
- **GPIO**: 30 programmierbare Pins
- **ADC**: 18 × 12-bit Kanäle
- **PWM**: Servo-Steuerung für Parkbügel

### **SIM7600G-H Features:**
- **4G LTE**: Cat-1 (10 Mbps down, 5 Mbps up)
- **GPS**: GNSS Multi-Constellation
- **SMS**: Backup-Kommunikation
- **HTTP/MQTT**: Cloud-Integration
- **Stromverbrauch**: <2W aktiv, <5mA sleep

### **Stromversorgung:**
- **Kapazität**: 2× 3000mAh = 6000mAh total
- **Spannung**: 7.4V nominal (6.0-8.4V)
- **Laufzeit**: ~48h Dauerbetrieb, >7 Tage Standby
- **Regler**: Pololu garantiert stabile 5V/2A

---

## 🚀 **ENTWICKLUNGS-ROADMAP**

### **PHASE 1: Hardware Assembly** (Woche 1)
- [ ] ESP32 Breadboard-Setup
- [ ] Grundlegende GPIO Tests
- [ ] WiFi Verbindung testen
- [ ] Servo-Steuerung implementieren

### **PHASE 2: Sensor Integration** (Woche 2)
- [ ] Hall-Sensor kalibrieren
- [ ] Fahrzeugerkennung programmieren
- [ ] Parkbügel-Automatik entwickeln
- [ ] Lokale Tests ohne Cloud

### **PHASE 3: 4G Connectivity** (Woche 3)
- [ ] SIM7600G-H Modul einbinden
- [ ] AT Commands testen
- [ ] HTTP API Calls zu gashis.ch
- [ ] GPS Position auslesen

### **PHASE 4: Cloud Integration** (Woche 4)
- [ ] Parkplatz-Status Upload
- [ ] Reservierungs-Download
- [ ] Real-time Updates
- [ ] Fehlerbehandlung

### **PHASE 5: Field Testing** (Woche 5)
- [ ] Outdoor Installation
- [ ] Wetterfestigkeit testen
- [ ] Batterielaufzeit messen
- [ ] Performance-Optimierung

---

## 🔌 **VERKABELUNG PLAN**

### **ESP32 Pin-Belegung:**
```
ESP32 GPIO | Komponente        | Funktion
-----------|-------------------|-------------------
GPIO 18    | SG92R Servo      | PWM Signal (Parkbügel)
GPIO 19    | Hall Sensor      | Digital Input (Fahrzeug)
GPIO 21    | SIM7600 RX       | UART Communication  
GPIO 22    | SIM7600 TX       | UART Communication
GPIO 2     | Status LED       | Debug/Status Anzeige
5V         | Servo Power      | Über Pololu Regler
3.3V       | Hall Sensor      | ESP32 interne Versorgung
GND        | Common Ground    | Alle Module
```

### **Stromversorgung Schema:**
```
18650 x2 (7.4V) → Pololu S13V20F5 → 5V/2A
                      ↓
              ┌───────┼───────┐
              ▼       ▼       ▼
           ESP32   Servo   SIM7600G
           (3.3V)  (5V)    (4V)
```

---

## 📱 **SOFTWARE INTEGRATION**

### **Arduino IDE Setup:**
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// Hardware Pins
#define SERVO_PIN 18
#define HALL_PIN 19  
#define LED_PIN 2

// API Endpoints
const char* API_BASE = "https://gashis.ch/parking/api/";
const char* WIFI_SSID = "YourWiFi";
const char* WIFI_PASS = "password";

Servo parkingBarrier;
```

### **Cloud API Calls:**
- **GET** `/parking-spots.php` - Aktueller Status
- **POST** `/update-spot.php` - Status ändern
- **GET** `/reservations.php` - Neue Reservierungen
- **POST** `/heartbeat.php` - System-Health

---

## 🛠️ **ENTWICKLUNGS-TOOLS**

### **Benötigte Software:**
- **Arduino IDE** 2.x mit ESP32 Board Package
- **CP2102 Driver** für ESP32 USB-Kommunikation  
- **SIM Card Manager** für 4G Modul Tests
- **Serial Monitor** für Debugging
- **Postman** für API Testing

### **Bibliotheken:**
```cpp
// Core ESP32 Libraries
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Hardware Control  
#include <ESP32Servo.h>
#include <HardwareSerial.h>

// 4G Communication
#include <TinyGSM.h>
```

---

## 🔧 **NEXT STEPS**

### **Sofort nach Lieferung:**
1. **Komponenten prüfen** - Vollständigkeit & Funktionalität
2. **ESP32 flashen** - Erste "Hello World" über Serial
3. **Breadboard aufbauen** - Schaltplan nach Pin-Belegung
4. **Servo testen** - Grundlegende Bewegung programmieren

### **Integration mit bestehender App:**
- Deine gashis.ch/parking App ist bereits live
- API Endpoints sind funktionsfähig
- Hardware wird als neuer Parkplatz registriert
- Real-time Updates über 4G Modul

### **Praktische Tipps:**
- **Beginn ohne 4G**: Erst WiFi für lokale Tests
- **Servo-Kalibrierung**: 90° = offen, 0° = geschlossen  
- **Hall-Sensor**: Magnet am Fahrzeug oder Bodenbefestigung
- **Power Management**: Sleep-Modi für Batterieschonung

---

## 📞 **SUPPORT & RESSOURCEN**

### **Hardware-Dokumentation:**
- **ESP32**: [Espressif Official Docs](https://docs.espressif.com/projects/esp-idf/en/latest/)
- **SIM7600G-H**: [Waveshare Wiki](https://www.waveshare.com/wiki/SIM7600G-H_4G_HAT_(B))
- **SG92R Servo**: Standard 50Hz PWM, 1-2ms Pulse Width

### **Code-Beispiele:**
- ESP32 WiFi Client Examples
- TinyGSM 4G HTTP Examples  
- Arduino Servo Library Tutorials

---

*Hardware-Status: ✅ Vollständig bestellt*  
*Nächster Schritt: Warten auf Lieferung & Development Setup*  
*Projektstart: Nach Hardware-Ankunft*

---

**🎉 GLÜCKWUNSCH! Du hast eine professionelle, durchdachte Hardware-Liste für deinen Smart Parking Prototypen zusammengestellt. Das System wird perfekt mit deiner bereits funktionierenden gashis.ch/parking App integrieren!**
