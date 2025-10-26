# 🚀 ENTWICKLUNGS-SETUP - ESP32 Smart Parking Prototyp
## Schritt-für-Schritt Anleitung nach Hardware-Ankunft

*Start-Guide für deinen ESP32 Smart Parking Prototypen*

---

## 📦 **TAG 1: UNBOXING & BASIC SETUP**

### **1. Hardware-Check (5 Min)**
```
✅ ESP32 Dev Board (NodeMCU/WROOM-32)
✅ SIM7600G-H 4G LTE Modul  
✅ SG92R Micro Servo
✅ Hall-Sensor A3144
✅ 2x 18650 Li-Ion Akkus + Halter
✅ Pololu S13V20F5 Step-Up/Down Regler
✅ Dupont Jumper Kabel Set
✅ Breadboard (400 Punkte)
✅ Acryl-Prototypenplatte
✅ M3 Nylon Abstandshalter Set
```

### **2. Software Installation (15 Min)**
```bash
# Arduino IDE herunterladen & installieren
# https://www.arduino.cc/en/software

# ESP32 Board Package installieren:
# Tools → Board → Boards Manager → "ESP32" suchen → installieren

# Benötigte Libraries installieren:
# Tools → Manage Libraries → folgende suchen & installieren:
- WiFi (bereits in ESP32 Core)
- HTTPClient (bereits in ESP32 Core) 
- ArduinoJson
- ESP32Servo
```

### **3. Erster Test - "Hello World" (10 Min)**
```cpp
// Datei: esp32_hello_world.ino
void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);  // Built-in LED
}

void loop() {
  digitalWrite(2, HIGH);
  Serial.println("ESP32 Smart Parking - System Running!");
  delay(1000);
  digitalWrite(2, LOW); 
  delay(1000);
}
```

**Upload Test:**
- ESP32 via USB verbinden
- Board: "ESP32 Dev Module" wählen
- Port: richtige COM-Port wählen
- Upload! → LED sollte blinken

---

## 🔧 **TAG 2: BREADBOARD AUFBAU**

### **Verkabelung Schema:**
```
ESP32 GPIO | Komponente           | Kabel-Farbe
-----------|---------------------|-------------
GPIO 18    | SG92R Servo (Signal)| Gelb
GPIO 19    | Hall Sensor (Out)   | Grün  
GPIO 2     | Status LED          | Blau
5V         | Servo Power (Red)   | Rot
3.3V       | Hall Sensor VCC     | Orange
GND        | Common Ground       | Schwarz
```

### **Stromversorgung Setup:**
1. **18650 Akkus** in Halter einsetzen (→ 7.4V)
2. **Pololu Regler** Eingänge an Akku-Halter
3. **5V Output** zu Breadboard Powerrail
4. **ESP32** über USB oder 5V→3.3V versorgen

### **Breadboard Layout:**
```
Power Rails:  [+5V] [GND]
                |     |
ESP32:     [3.3V][GPIO18][GPIO19][GPIO2][GND]
                |       |       |      |
Components: Servo    Hall    LED   Common
```

---

## 💻 **TAG 3: GRUNDFUNKTIONEN PROGRAMMIEREN**

### **Hall-Sensor Test:**
```cpp
// Datei: hall_sensor_test.ino
#define HALL_PIN 19

void setup() {
  Serial.begin(115200);
  pinMode(HALL_PIN, INPUT_PULLUP);
}

void loop() {
  int hallValue = digitalRead(HALL_PIN);
  
  if (hallValue == LOW) {
    Serial.println("🚗 FAHRZEUG ERKANNT!");
  } else {
    Serial.println("🅿️ PARKPLATZ FREI");
  }
  
  delay(500);
}
```

### **Servo-Steuerung Test:**
```cpp
// Datei: servo_test.ino
#include <ESP32Servo.h>

#define SERVO_PIN 18
Servo parkingBarrier;

void setup() {
  Serial.begin(115200);
  parkingBarrier.attach(SERVO_PIN);
}

void loop() {
  Serial.println("Bügel HOCH (gesperrt)");
  parkingBarrier.write(90);  // Bügel hoch
  delay(3000);
  
  Serial.println("Bügel RUNTER (frei)");  
  parkingBarrier.write(0);   // Bügel runter
  delay(3000);
}
```

---

## 🌐 **TAG 4: WIFI & API INTEGRATION**

### **WiFi Verbindung:**
```cpp
// Datei: wifi_api_test.ino
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "DEIN_WIFI_NAME";
const char* password = "DEIN_WIFI_PASSWORT";
const char* apiBase = "https://gashis.ch/parking/api/";

void setup() {
  Serial.begin(115200);
  
  // WiFi verbinden
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Verbinde WiFi...");
  }
  
  Serial.println("WiFi verbunden!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  testApiCall();
  delay(10000);  // Alle 10 Sekunden
}

void testApiCall() {
  HTTPClient http;
  http.begin("https://gashis.ch/parking/api/parking-spots.php");
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    Serial.println("✅ API Response:");
    Serial.println(payload);
  } else {
    Serial.print("❌ HTTP Error: ");
    Serial.println(httpCode);
  }
  
  http.end();
}
```

---

## 📱 **TAG 5: KOMPLETT-SYSTEM INTEGRATION**

### **Vollständiger Prototyp Code:**
```cpp
// Datei: smart_parking_prototype.ino
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// Hardware Pins
#define SERVO_PIN 18
#define HALL_PIN 19  
#define LED_PIN 2

// WiFi & API
const char* ssid = "DEIN_WIFI";
const char* password = "DEIN_PASSWORT";
const char* apiBase = "https://gashis.ch/parking/api/";

// Hardware Objects
Servo parkingBarrier;

// System Status
bool parkingSpotOccupied = false;
bool barrierUp = false;
unsigned long lastApiUpdate = 0;
const unsigned long apiInterval = 30000; // 30 Sekunden

void setup() {
  Serial.begin(115200);
  
  // Hardware initialisieren
  pinMode(HALL_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  parkingBarrier.attach(SERVO_PIN);
  
  // WiFi verbinden
  connectWiFi();
  
  // System bereit
  Serial.println("🚀 Smart Parking System ONLINE!");
  blinkStatus(3); // 3x blinken = System ready
}

void loop() {
  // Hall-Sensor lesen
  checkVehiclePresence();
  
  // Parkbügel steuern  
  controlParkingBarrier();
  
  // Status-LED aktualisieren
  updateStatusLED();
  
  // API Updates (alle 30 Sekunden)
  if (millis() - lastApiUpdate > apiInterval) {
    sendStatusUpdate();
    lastApiUpdate = millis();
  }
  
  delay(100); // System-Takt
}

void checkVehiclePresence() {
  bool currentState = (digitalRead(HALL_PIN) == LOW);
  
  if (currentState != parkingSpotOccupied) {
    parkingSpotOccupied = currentState;
    
    if (parkingSpotOccupied) {
      Serial.println("🚗 FAHRZEUG ANGEKOMMEN!");
    } else {
      Serial.println("🅿️ FAHRZEUG WEGGEFAHREN!");  
    }
    
    // Sofortiges API Update bei Statuswechsel
    sendStatusUpdate();
  }
}

void controlParkingBarrier() {
  bool shouldBarrierBeUp = parkingSpotOccupied;
  
  if (shouldBarrierBeUp != barrierUp) {
    barrierUp = shouldBarrierBeUp;
    
    if (barrierUp) {
      Serial.println("🔴 BÜGEL HOCH - GESPERRT");
      parkingBarrier.write(90);
    } else {
      Serial.println("🟢 BÜGEL RUNTER - FREI");
      parkingBarrier.write(0);
    }
  }
}

void updateStatusLED() {
  if (parkingSpotOccupied) {
    digitalWrite(LED_PIN, HIGH); // LED an = besetzt
  } else {
    // LED blinken = frei
    digitalWrite(LED_PIN, (millis() / 500) % 2);
  }
}

void sendStatusUpdate() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    return;
  }
  
  HTTPClient http;
  http.begin("https://gashis.ch/parking/api/update-spot.php");
  http.addHeader("Content-Type", "application/json");
  
  // JSON Payload erstellen
  StaticJsonDocument<200> doc;
  doc["spot_id"] = "hardware_prototype_001";
  doc["status"] = parkingSpotOccupied ? "occupied" : "free";
  doc["timestamp"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpCode = http.POST(jsonString);
  if (httpCode == 200) {
    Serial.println("✅ Status an App gesendet");
  } else {
    Serial.print("❌ API Fehler: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("WiFi verbinden");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("✅ WiFi verbunden! IP: ");
  Serial.println(WiFi.localIP());
}

void blinkStatus(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}
```

---

## 🔧 **DEBUGGING & TROUBLESHOOTING**

### **Häufige Probleme:**
1. **ESP32 wird nicht erkannt:** CP2102 Treiber installieren
2. **WiFi Verbindung fehlschlägt:** SSID/Passwort prüfen
3. **Servo zuckt:** Stromversorgung stabilisieren (Pololu Regler)
4. **Hall-Sensor unzuverlässig:** Pull-up Widerstand prüfen
5. **API Calls fehlen:** CORS & HTTPS Zertifikate prüfen

### **Serial Monitor Commands:**
```cpp
// Zusätzliche Debug-Funktionen hinzufügen:
void printSystemStatus() {
  Serial.println("=== SYSTEM STATUS ===");
  Serial.print("WiFi: "); Serial.println(WiFi.status() == WL_CONNECTED ? "✅" : "❌");
  Serial.print("Fahrzeug: "); Serial.println(parkingSpotOccupied ? "🚗 Ja" : "🅿️ Nein");
  Serial.print("Bügel: "); Serial.println(barrierUp ? "🔴 Hoch" : "🟢 Runter");
  Serial.print("Uptime: "); Serial.print(millis()/1000); Serial.println(" Sekunden");
  Serial.println("==================");
}
```

---

## 🎯 **NEXT LEVEL: 4G INTEGRATION**

### **Nach erfolgreichem WiFi-Test:**
1. **SIM7600G-H Modul** verkabeln (UART)
2. **TinyGSM Library** für 4G verwenden
3. **GPS Position** auslesen
4. **Offline-Modus** implementieren (lokaler Speicher)
5. **OTA Updates** für Remote-Wartung

### **Produktiv-Setup:**
- **Wetterfestes Gehäuse** für Outdoor-Installation
- **Solar-Panel** für Dauerstrom-Versorgung  
- **Mehrere Parkplätze** parallel überwachen
- **Web-Dashboard** für Live-Monitoring

---

## 📞 **SUPPORT & RESSOURCEN**

### **Bei Problemen:**
1. **Serial Monitor** verwenden für Debug-Output
2. **Voltmeter** prüft Stromversorgung
3. **WiFi Scanner** testet Netzwerk-Verbindung
4. **API-Test** mit Postman/Browser

### **Wichtige Links:**
- ESP32 Pinout: https://randomnerdtutorials.com/esp32-pinout-reference-gpios/
- Arduino ESP32 Core: https://github.com/espressif/arduino-esp32
- deine Live-App: https://gashis.ch/parking/

---

**🎉 Glückwunsch! Mit diesem Setup hast du einen vollständig funktionsfähigen Smart Parking Prototypen, der bereits mit deiner Live-App auf gashis.ch integriert ist!**

*Ready for Hardware Development! 🚀*
