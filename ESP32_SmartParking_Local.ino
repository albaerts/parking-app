/*
 * Smart Parking ESP32 Prototyp - SIM7600 LTE
 * 
 * Hardware:
 * - ESP32 Dev Board
 * - SIM7600 Modem (LTE/4G Datenverbindung)
 * - Hall Sensor (Magnetsensor) für Fahrzeugerkennung
 * - Servo SG92R für Parkbügel
 * 
 * Funktionen:
 * - Verbindet sich über SIM7600 mit 4G/LTE
 * - Sendet Telemetrie-Daten (Belegung, Batterie, Signal)
 * - Holt Commands vom Server (raise_barrier, lower_barrier)
 * - Steuert Servo basierend auf Commands
 * 
 * Setup:
 * 1. Erstelle ESP32_CONFIG_LOCAL.h mit deinen Einstellungen
 * 2. SIM-Karte einlegen (mit Daten-Abo)
 * 3. Lade dieses Sketch auf ESP32 hoch
 * 4. Öffne Serial Monitor (115200 baud)
 * 5. Weise das Gerät in der Web-App zu
 */

#include <ArduinoJson.h>
#include <ESP32Servo.h>

// Lade lokale Konfiguration
// WICHTIG: Erstelle diese Datei zuerst und passe die Werte an!
#include "ESP32_CONFIG_LOCAL.h"

// SIM7600 Hardware Serial
#define SIM7600_SERIAL Serial2
#define SIM7600_BAUD 115200

// ========== GLOBALS ==========
Servo barrierServo;
unsigned long lastPollTime = 0;
unsigned long lastTelemetryTime = 0;

// Sensor-Zustand
int hallBaseline = 0;
bool isOccupied = false;
float batteryVoltage = 3.7;  // Simuliert, da USB-Power
int wifiRSSI = 0;

// Servo-Zustand
bool barrierIsUp = false;

// ========== SETUP ==========
void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1000);
  
  Serial.println("\n\n==================================");
  Serial.println("ESP32 Smart Parking Prototyp");
  Serial.println("==================================");
  
  // Status LED
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);
  
  // Hall-Sensor
  pinMode(HALL_SENSOR_PIN, INPUT);
  
  // Servo
  barrierServo.attach(SERVO_PIN);
  barrierServo.write(SERVO_POS_DOWN);  // Start: Bügel unten
  barrierIsUp = false;
  
  Serial.println("\n1. WiFi verbinden...");
  connectWiFi();
  
  Serial.println("\n2. Hall-Sensor kalibrieren...");
  calibrateHallSensor();
  
  Serial.println("\n3. Test-Telemetrie senden...");
  sendTelemetry();
  
  Serial.println("\n✅ Setup abgeschlossen!");
  Serial.println("==================================");
  Serial.print("Device-ID: ");
  Serial.println(DEVICE_ID);
  Serial.print("Server: ");
  Serial.println(LOCAL_API_BASE);
  Serial.println("==================================\n");
  
  digitalWrite(STATUS_LED, HIGH);  // Bereit
}

// ========== MAIN LOOP ==========
void loop() {
  // Überprüfe WiFi-Verbindung
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️  WiFi getrennt, verbinde neu...");
    connectWiFi();
  }
  
  // 1. Commands vom Server abholen (alle 10s)
  if (millis() - lastPollTime >= POLL_INTERVAL_MS) {
    lastPollTime = millis();
    pollCommands();
  }
  
  // 2. Telemetrie senden (alle 30s)
  if (millis() - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = millis();
    updateSensors();
    sendTelemetry();
  }
  
  delay(100);  // Kleine Pause
}

// ========== WIFI ==========
void connectWiFi() {
  Serial.print("Verbinde mit WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi verbunden!");
    Serial.print("IP-Adresse: ");
    Serial.println(WiFi.localIP());
    wifiRSSI = WiFi.RSSI();
    Serial.print("Signal: ");
    Serial.print(wifiRSSI);
    Serial.println(" dBm");
  } else {
    Serial.println("\n❌ WiFi-Verbindung fehlgeschlagen!");
    Serial.println("Überprüfe SSID und Passwort in ESP32_CONFIG_LOCAL.h");
  }
}

// ========== HALL SENSOR ==========
void calibrateHallSensor() {
  if (!AUTO_CALIBRATE) {
    hallBaseline = HALL_THRESHOLD;
    Serial.println("Auto-Kalibrierung deaktiviert, nutze Schwellwert");
    return;
  }
  
  Serial.println("Kalibriere Hall-Sensor...");
  Serial.println("(Stelle sicher, dass KEIN Auto auf dem Platz steht)");
  
  delay(2000);  // 2 Sekunden warten
  
  // 10 Messungen nehmen
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(HALL_SENSOR_PIN);
    delay(100);
  }
  
  hallBaseline = sum / 10;
  Serial.print("✅ Baseline: ");
  Serial.println(hallBaseline);
}

void updateSensors() {
  // Hall-Sensor lesen
  int hallValue = analogRead(HALL_SENSOR_PIN);
  int difference = abs(hallValue - hallBaseline);
  
  // Belegung erkennen (wenn Magnet zu nah)
  bool wasOccupied = isOccupied;
  isOccupied = (difference > HALL_THRESHOLD);
  
  if (isOccupied != wasOccupied) {
    Serial.print("🚗 Belegung geändert: ");
    Serial.println(isOccupied ? "BELEGT" : "FREI");
  }
  
  // WiFi Signal aktualisieren
  wifiRSSI = WiFi.RSSI();
  
  // Batteriespannung (simuliert bei USB-Power)
  // Bei echter Batterie: analogRead(BAT_PIN) * (3.3 / 4095.0) * 2
  batteryVoltage = 3.7;
  
  if (DEBUG_VERBOSE) {
    Serial.print("Hall: ");
    Serial.print(hallValue);
    Serial.print(" (Baseline: ");
    Serial.print(hallBaseline);
    Serial.print(", Diff: ");
    Serial.print(difference);
    Serial.print(") | ");
    Serial.print(isOccupied ? "BELEGT" : "FREI");
    Serial.print(" | RSSI: ");
    Serial.print(wifiRSSI);
    Serial.println(" dBm");
  }
}

// ========== SERVO ==========
void raiseBarrier() {
  if (barrierIsUp) {
    Serial.println("⚠️  Bügel ist bereits oben");
    return;
  }
  
  Serial.println("⬆️  Hebe Bügel...");
  barrierServo.write(SERVO_POS_UP);
  delay(SERVO_SPEED_MS);
  barrierIsUp = true;
  Serial.println("✅ Bügel oben");
}

void lowerBarrier() {
  if (!barrierIsUp) {
    Serial.println("⚠️  Bügel ist bereits unten");
    return;
  }
  
  Serial.println("⬇️  Senke Bügel...");
  barrierServo.write(SERVO_POS_DOWN);
  delay(SERVO_SPEED_MS);
  barrierIsUp = false;
  Serial.println("✅ Bügel unten");
}

// ========== API: COMMANDS ABHOLEN ==========
void pollCommands() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = String(LOCAL_API_BASE) + "/hardware/" + String(DEVICE_ID) + "/commands";
  
  http.begin(url);
  http.setTimeout(5000);
  
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parse JSON
    DynamicJsonDocument doc(2048);
    DeserializationError error = deserializeJson(doc, payload);
    
    if (error) {
      Serial.print("❌ JSON Parse Fehler: ");
      Serial.println(error.c_str());
      http.end();
      return;
    }
    
    JsonArray commands = doc["commands"].as<JsonArray>();
    
    if (commands.size() > 0) {
      Serial.print("📥 ");
      Serial.print(commands.size());
      Serial.println(" Command(s) empfangen");
      
      for (JsonObject cmd : commands) {
        String command = cmd["command"].as<String>();
        int cmdId = cmd["id"];
        
        Serial.print("  → Command #");
        Serial.print(cmdId);
        Serial.print(": ");
        Serial.println(command);
        
        // Command ausführen
        if (command == "raise_barrier") {
          raiseBarrier();
        } else if (command == "lower_barrier") {
          lowerBarrier();
        } else if (command == "reset") {
          Serial.println("🔄 Reset...");
          ESP.restart();
        } else {
          Serial.print("⚠️  Unbekannter Command: ");
          Serial.println(command);
        }
      }
    } else {
      if (DEBUG_VERBOSE) {
        Serial.println("✓ Keine neuen Commands");
      }
    }
  } else if (httpCode > 0) {
    Serial.print("❌ HTTP Fehler: ");
    Serial.println(httpCode);
  } else {
    Serial.print("❌ Verbindungsfehler: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  
  http.end();
}

// ========== API: TELEMETRIE SENDEN ==========
void sendTelemetry() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = String(LOCAL_API_BASE) + "/hardware/" + String(DEVICE_ID) + "/telemetry";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  
  // JSON erstellen
  DynamicJsonDocument doc(512);
  doc["battery_level"] = batteryVoltage;
  doc["rssi"] = wifiRSSI;
  doc["occupancy"] = isOccupied ? "occupied" : "free";
  
  // Optional: Magnetometer-Daten (wenn vorhanden)
  JsonObject mag = doc.createNestedObject("last_mag");
  mag["x"] = 0.0;
  mag["y"] = 0.0;
  mag["z"] = 0.0;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  if (DEBUG_VERBOSE) {
    Serial.println("📤 Sende Telemetrie:");
    Serial.print("   ");
    Serial.println(jsonString);
  }
  
  int httpCode = http.POST(jsonString);
  
  if (httpCode == 200) {
    Serial.println("✅ Telemetrie gesendet");
  } else if (httpCode > 0) {
    Serial.print("❌ HTTP Fehler: ");
    Serial.println(httpCode);
    Serial.println(http.getString());
  } else {
    Serial.print("❌ Verbindungsfehler: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  
  http.end();
}
