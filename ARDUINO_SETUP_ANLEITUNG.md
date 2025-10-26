# ⚙️ ARDUINO IDE SETUP - SCHRITT FÜR SCHRITT

## 🎯 **VORBEREITUNG (5 MINUTEN)**

### **Schritt 1: Arduino IDE installieren**
```
🌐 Gehe zu: https://arduino.cc/en/software
📥 Download: "Arduino IDE 2.3.2" für macOS
📁 .dmg Datei öffnen
🖱️ Arduino IDE in den Programme-Ordner ziehen
✅ Installation fertig!
```

### **Schritt 2: Arduino IDE starten**
```
🚀 Arduino IDE öffnen
⚠️ Falls Sicherheitswarnung: "Trotzdem öffnen"
✅ Arduino IDE sollte starten
```

---

## 📱 **ESP32 BOARD HINZUFÜGEN**

### **Schritt 3: ESP32 Package installieren**
```
🔧 Arduino IDE → Einstellungen/Preferences
📋 "Additional Board Manager URLs" Feld finden
📝 Folgende URL einfügen:
    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
✅ OK klicken
```

### **Schritt 4: ESP32 Board Manager**
```
🔧 Tools → Board → Boards Manager...
🔍 Suche nach: "esp32"
📦 "esp32 by Espressif Systems" finden
⬇️ "Install" klicken (kann 2-3 Minuten dauern)
✅ Installation fertig!
```

### **Schritt 5: Board auswählen**
```
🔧 Tools → Board → ESP32 Arduino
📱 "ESP32 Dev Module" auswählen
✅ Board ist jetzt bereit!
```

---

## 📚 **BENÖTIGTE BIBLIOTHEKEN**

### **Schritt 6: Libraries installieren**
```
🔧 Tools → Manage Libraries...
🔍 Suche und installiere folgende:

1️⃣ "WiFi" by Arduino (meist schon installiert)
2️⃣ "HTTPClient" by Adrian McEwen 
3️⃣ "ArduinoJson" by Benoit Blanchon
4️⃣ "ESP32Servo" by Kevin Harrington

Für jede Library:
📝 Namen eingeben → Suchen → Install klicken
```

---

## 🔌 **USB VERBINDUNG TESTEN**

### **Schritt 7: ESP32 anschließen**
```
📦 ESP32 aus dem Paket nehmen
🔌 USB-C Kabel anschließen (ESP32 ↔ Mac)
💡 ESP32 sollte blaue LED zeigen
```

### **Schritt 8: Port auswählen**
```
🔧 Tools → Port
📱 Suche nach "/dev/cu.usbserial-..." oder ähnlich
✅ Diesen Port auswählen
```

### **Schritt 9: Blink Test**
```
📂 File → Examples → 01.Basics → Blink
📝 Code wird geladen
⬆️ Upload Button (Pfeil) klicken
⏳ Warten bis "Done uploading" erscheint
💡 ESP32 LED sollte blinken!
✅ ESP32 funktioniert!
```

---

## 💻 **QUICK & DIRTY PARKING CODE**

### **Schritt 10: Parking Code vorbereiten**
```cpp
// SMART PARKING - QUICK & DIRTY VERSION
#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// WIFI EINSTELLUNGEN (ÄNDERE HIER DEINE DATEN!)
const char* ssid = "DEIN_HANDY_HOTSPOT";      // Handy-Hotspot Name
const char* password = "DEIN_HOTSPOT_PASSWORD"; // Handy-Hotspot Passwort

// SERVER EINSTELLUNGEN
const char* serverURL = "http://192.168.43.1:3000/api/parking-status"; // Handy IP

// PIN DEFINITIONEN
const int trigPin = 12;    // Ultraschall Trigger
const int echoPin = 13;    // Ultraschall Echo
const int servoPin = 14;   // Servo Motor
const int ledPin = 2;      // Status LED

Servo parkingBarrier;

void setup() {
  Serial.begin(115200);
  Serial.println("🚗 Smart Parking System startet...");
  
  // Pins konfigurieren
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledPin, OUTPUT);
  
  // Servo initialisieren
  parkingBarrier.attach(servoPin);
  parkingBarrier.write(0);  // Bügel HOCH (frei)
  
  // WiFi verbinden
  WiFi.begin(ssid, password);
  Serial.print("Verbinde mit WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("✅ WiFi verbunden!");
  Serial.print("IP Adresse: ");
  Serial.println(WiFi.localIP());
  
  digitalWrite(ledPin, HIGH); // Status LED an
}

void loop() {
  // Entfernung messen
  float distance = measureDistance();
  
  if (distance < 30.0 && distance > 0) {
    // Auto erkannt!
    Serial.println("🚗 Auto erkannt!");
    parkingBarrier.write(90);  // Bügel RUNTER (besetzt)
    sendParkingStatus("occupied");
    
  } else {
    // Parkplatz frei
    Serial.println("✅ Parkplatz frei");
    parkingBarrier.write(0);   // Bügel HOCH (frei)
    sendParkingStatus("free");
  }
  
  delay(2000); // Alle 2 Sekunden prüfen
}

float measureDistance() {
  // Ultraschall Messung
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;
  
  Serial.print("Entfernung: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  return distance;
}

void sendParkingStatus(String status) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    String jsonPayload = "{\"spot_id\":\"quick-dirty-01\",\"status\":\"" + status + "\",\"timestamp\":\"" + String(millis()) + "\"}";
    
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("✅ Status gesendet: " + status);
      Serial.println("Server Antwort: " + response);
    } else {
      Serial.println("❌ Fehler beim Senden: " + String(httpResponseCode));
    }
    
    http.end();
  } else {
    Serial.println("❌ WiFi nicht verbunden!");
  }
}
```

### **Schritt 11: Code anpassen**
```
📝 Zeile 7: "DEIN_HANDY_HOTSPOT" → Dein Hotspot-Name eintragen
📝 Zeile 8: "DEIN_HOTSPOT_PASSWORD" → Dein Hotspot-Passwort eintragen
📝 Zeile 11: IP-Adresse deines Handys eintragen (findest du in Hotspot-Einstellungen)
```

---

## 🔧 **HARDWARE VERDRAHTUNG**

### **Schritt 12: Komponenten verbinden**
```
ESP32 CONNECTIONS:
├─ Ultraschall Sensor JSN-SR04T:
│   ├─ VCC → 5V (ESP32)
│   ├─ GND → GND (ESP32)
│   ├─ Trig → GPIO 12
│   └─ Echo → GPIO 13
│   
├─ Servo Motor SG90:
│   ├─ Rot → 5V (ESP32)
│   ├─ Braun/Schwarz → GND (ESP32)
│   └─ Orange/Gelb → GPIO 14
│   
└─ Power Bank → ESP32 USB-C

BREADBOARD LAYOUT:
┌─────────────────────────┐
│  [ESP32 Dev Board]      │
│  │   │   │   │   │   │  │
│  5V GND 12  13  14  2   │
│  │   │   │   │   │   │  │
│  │   ├───┼───┼───┼───┤  │
│  │   │   │   │   │   │  │
│ Sensor │  T   E   S   L │
│ Power  │  r   c   e   E │
│ Bank   │  i   h   r   D │
│        │  g   o   v     │
│        │      o        │
└─────────────────────────┘
```

---

## ✅ **BEREIT FÜR DIE PAKETE!**

### **Was passiert nach der Amazon-Lieferung:**
```
📦 PAKETE ANKOMMEN
├─ ESP32 auspacken
├─ Komponenten auf Breadboard stecken (5 Min)
├─ Code in Arduino IDE laden
├─ Upload auf ESP32 (30 Sek)
├─ Handy-Hotspot aktivieren
├─ Serial Monitor öffnen → sollte "WiFi verbunden!" zeigen
├─ Hand vor Sensor halten → Servo sollte sich bewegen!
└─ ✅ FUNKTIONIERT!

🚗 IN WASSERDICHTE BOX EINBAUEN
├─ Löcher für Kabel bohren
├─ ESP32 + Breadboard reinlegen
├─ Sensor vorne montieren
├─ Servo als Mini-Bügel hinten
├─ Power Bank anschließen
└─ ✅ OUTDOOR-READY!
```

**🎯 Du bist jetzt bereit! Sobald die Amazon-Pakete da sind, kannst du in 30 Minuten loslegen! 🚀**
