/*
 * Smart Parking ESP32 Prototyp - SIM7600 LTE
 * 
 * Hardware:
 * - ESP32 Dev Board
 * - SIM7600E Modem (LTE/4G mit Datenverbindung)
 * - Hall Sensor (Magnetsensor) für Fahrzeugerkennung
 * - Servo SG92R für Parkbügel
 * 
 * Verbindung:
 * - SIM7600 TX → ESP32 RX (GPIO16)
 * - SIM7600 RX → ESP32 TX (GPIO17)
 * - SIM7600 PWR → ESP32 GPIO4
 * - Hall Sensor → ESP32 GPIO32
 * - Servo → ESP32 GPIO25
 * 
 * Funktionen:
 * - Verbindet sich über SIM7600 mit 4G/LTE
 * - Sendet Telemetrie-Daten über HTTP
 * - Holt Commands vom Server
 * - Steuert Parkbügel-Servo
 */

#include <ArduinoJson.h>
#include <ESP32Servo.h>

// Lade Konfiguration
#include "ESP32_CONFIG_LOCAL.h"

// SIM7600 Serial
#define SIM7600_SERIAL Serial2
#define SIM7600_RX 16
#define SIM7600_TX 17
#define SIM7600_PWR 4
#define SIM7600_BAUD 115200

// ========== GLOBALS ==========
Servo barrierServo;
unsigned long lastPollTime = 0;
unsigned long lastTelemetryTime = 0;

// Sensor-Zustand
int hallBaseline = 0;
bool isOccupied = false;
float batteryVoltage = 3.7;
int signalQuality = 0;  // CSQ (0-31, 99=unknown)

// Servo-Zustand
bool barrierIsUp = false;

// Modem-Status
bool modemReady = false;
bool networkRegistered = false;
bool gprsConnected = false;

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n\n==================================");
  Serial.println("ESP32 Smart Parking - SIM7600");
  Serial.println("==================================");
  
  // Status LED
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);
  
  // SIM7600 Power Key
  pinMode(SIM7600_PWR, OUTPUT);
  digitalWrite(SIM7600_PWR, HIGH);
  
  // Hall-Sensor
  pinMode(HALL_SENSOR_PIN, INPUT);
  
  // Servo
  barrierServo.attach(SERVO_PIN);
  barrierServo.write(SERVO_POS_DOWN);
  barrierIsUp = false;
  
  // SIM7600 Serial starten
  SIM7600_SERIAL.begin(SIM7600_BAUD, SERIAL_8N1, SIM7600_RX, SIM7600_TX);
  
  Serial.println("\n1. SIM7600 Modem initialisieren...");
  initModem();
  
  Serial.println("\n2. Mit Mobilfunknetz verbinden...");
  connectNetwork();
  
  Serial.println("\n3. GPRS/LTE aktivieren...");
  connectGPRS();
  
  Serial.println("\n4. Hall-Sensor kalibrieren...");
  calibrateHallSensor();
  
  Serial.println("\n5. Test-Telemetrie senden...");
  sendTelemetry();
  
  Serial.println("\n✅ Setup abgeschlossen!");
  Serial.println("==================================");
  Serial.print("Device-ID: ");
  Serial.println(DEVICE_ID);
  Serial.print("Server: ");
  Serial.println(PRODUCTION_API_BASE);
  Serial.println("==================================\n");
  
  digitalWrite(STATUS_LED, HIGH);
}

// ========== MAIN LOOP ==========
void loop() {
  // Modem-Status prüfen
  if (!gprsConnected) {
    Serial.println("⚠️  GPRS getrennt, verbinde neu...");
    connectGPRS();
  }
  
  // 1. Commands abholen (alle 10s)
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
  
  delay(100);
}

// ========== SIM7600 MODEM ==========
void sendATCommand(const char* cmd, unsigned long timeout = 1000) {
  SIM7600_SERIAL.println(cmd);
  Serial.print("AT> ");
  Serial.println(cmd);
  
  unsigned long start = millis();
  String response = "";
  
  while (millis() - start < timeout) {
    while (SIM7600_SERIAL.available()) {
      char c = SIM7600_SERIAL.read();
      response += c;
      Serial.print(c);
    }
    if (response.indexOf("OK") != -1 || response.indexOf("ERROR") != -1) {
      break;
    }
  }
  
  delay(100);
}

String sendATCommandWithResponse(const char* cmd, unsigned long timeout = 2000) {
  SIM7600_SERIAL.println(cmd);
  
  unsigned long start = millis();
  String response = "";
  
  while (millis() - start < timeout) {
    while (SIM7600_SERIAL.available()) {
      response += (char)SIM7600_SERIAL.read();
    }
    if (response.indexOf("OK") != -1 || response.indexOf("ERROR") != -1) {
      break;
    }
  }
  
  return response;
}

void initModem() {
  Serial.println("Power on Modem...");
  digitalWrite(SIM7600_PWR, LOW);
  delay(2000);
  digitalWrite(SIM7600_PWR, HIGH);
  delay(10000);  // Warte auf Boot
  
  // Teste Kommunikation
  for (int i = 0; i < 5; i++) {
    sendATCommand("AT");
    String resp = sendATCommandWithResponse("AT");
    if (resp.indexOf("OK") != -1) {
      Serial.println("✅ Modem antwortet");
      modemReady = true;
      break;
    }
    delay(1000);
  }
  
  if (!modemReady) {
    Serial.println("❌ Modem antwortet nicht!");
    return;
  }
  
  // Echo ausschalten
  sendATCommand("ATE0");
  
  // Modem Info
  Serial.println("\nModem Info:");
  sendATCommand("ATI");  // Hersteller
  sendATCommand("AT+CGMM");  // Modell
  sendATCommand("AT+CGSN");  // IMEI
}

void connectNetwork() {
  Serial.println("Warte auf Netzwerk-Registrierung...");
  
  for (int i = 0; i < 30; i++) {
    String resp = sendATCommandWithResponse("AT+CREG?");
    
    // +CREG: 0,1 = registered (home)
    // +CREG: 0,5 = registered (roaming)
    if (resp.indexOf(",1") != -1 || resp.indexOf(",5") != -1) {
      Serial.println("✅ Im Netz registriert");
      networkRegistered = true;
      
      // Signal Quality
      resp = sendATCommandWithResponse("AT+CSQ");
      int csqStart = resp.indexOf("+CSQ: ") + 6;
      if (csqStart > 5) {
        String csqStr = resp.substring(csqStart, resp.indexOf(",", csqStart));
        signalQuality = csqStr.toInt();
        Serial.print("Signal: ");
        Serial.print(signalQuality);
        Serial.println("/31");
      }
      
      return;
    }
    
    Serial.print(".");
    delay(1000);
  }
  
  Serial.println("\n❌ Netzwerk-Registrierung fehlgeschlagen!");
}

void connectGPRS() {
  if (!networkRegistered) {
    Serial.println("❌ Nicht im Netz, kann GPRS nicht aktivieren");
    return;
  }
  
  Serial.println("Aktiviere GPRS/LTE...");
  
  // Set APN (für Swisscom, Salt, Sunrise)
  sendATCommand("AT+CGDCONT=1,\"IP\",\"gprs.swisscom.ch\"");  // Swisscom
  // sendATCommand("AT+CGDCONT=1,\"IP\",\"internet\"");  // Salt/Sunrise
  
  delay(1000);
  
  // Aktiviere PDP Context
  sendATCommand("AT+CGACT=1,1", 10000);
  
  delay(2000);
  
  // Check IP
  String resp = sendATCommandWithResponse("AT+CGPADDR=1");
  if (resp.indexOf("CGPADDR") != -1) {
    Serial.println("✅ GPRS verbunden");
    Serial.println(resp);
    gprsConnected = true;
  } else {
    Serial.println("❌ GPRS-Verbindung fehlgeschlagen");
  }
}

// ========== HTTP MIT SIM7600 ==========
String httpGET(const char* url) {
  if (!gprsConnected) {
    Serial.println("❌ GPRS nicht verbunden");
    return "";
  }
  
  // HTTP initialisieren
  sendATCommand("AT+HTTPTERM");  // Cleanup
  delay(500);
  sendATCommand("AT+HTTPINIT");
  delay(500);
  
  // CID setzen
  sendATCommand("AT+HTTPPARA=\"CID\",1");
  
  // URL setzen
  String urlCmd = "AT+HTTPPARA=\"URL\",\"" + String(url) + "\"";
  sendATCommand(urlCmd.c_str());
  
  // GET Request
  Serial.println("HTTP GET...");
  String resp = sendATCommandWithResponse("AT+HTTPACTION=0", 10000);
  
  // Warte auf Response
  delay(2000);
  
  // Lese Daten
  resp = sendATCommandWithResponse("AT+HTTPREAD", 5000);
  
  // Cleanup
  sendATCommand("AT+HTTPTERM");
  
  return resp;
}

String httpPOST(const char* url, const char* data) {
  if (!gprsConnected) {
    Serial.println("❌ GPRS nicht verbunden");
    return "";
  }
  
  // HTTP initialisieren
  sendATCommand("AT+HTTPTERM");
  delay(500);
  sendATCommand("AT+HTTPINIT");
  delay(500);
  
  // CID setzen
  sendATCommand("AT+HTTPPARA=\"CID\",1");
  
  // URL setzen
  String urlCmd = "AT+HTTPPARA=\"URL\",\"" + String(url) + "\"";
  sendATCommand(urlCmd.c_str());
  
  // Content-Type
  sendATCommand("AT+HTTPPARA=\"CONTENT\",\"application/json\"");
  
  // Daten vorbereiten
  int dataLen = strlen(data);
  String dataCmd = "AT+HTTPDATA=" + String(dataLen) + ",10000";
  sendATCommand(dataCmd.c_str());
  delay(500);
  
  // Daten senden
  SIM7600_SERIAL.println(data);
  Serial.print("POST Data: ");
  Serial.println(data);
  delay(500);
  
  // POST Request
  Serial.println("HTTP POST...");
  String resp = sendATCommandWithResponse("AT+HTTPACTION=1", 10000);
  
  delay(2000);
  
  // Lese Response
  resp = sendATCommandWithResponse("AT+HTTPREAD", 5000);
  
  // Cleanup
  sendATCommand("AT+HTTPTERM");
  
  return resp;
}

// ========== HALL SENSOR ==========
void calibrateHallSensor() {
  if (!AUTO_CALIBRATE) {
    hallBaseline = HALL_THRESHOLD;
    Serial.println("Auto-Kalibrierung deaktiviert");
    return;
  }
  
  Serial.println("Kalibriere Hall-Sensor...");
  delay(2000);
  
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
  int hallValue = analogRead(HALL_SENSOR_PIN);
  int difference = abs(hallValue - hallBaseline);
  
  bool wasOccupied = isOccupied;
  isOccupied = (difference > HALL_THRESHOLD);
  
  if (isOccupied != wasOccupied) {
    Serial.print("🚗 Belegung: ");
    Serial.println(isOccupied ? "BELEGT" : "FREI");
  }
  
  // Signal Quality aktualisieren
  String resp = sendATCommandWithResponse("AT+CSQ");
  int csqStart = resp.indexOf("+CSQ: ") + 6;
  if (csqStart > 5) {
    String csqStr = resp.substring(csqStart, resp.indexOf(",", csqStart));
    signalQuality = csqStr.toInt();
  }
  
  if (DEBUG_VERBOSE) {
    Serial.print("Hall: ");
    Serial.print(hallValue);
    Serial.print(" | ");
    Serial.print(isOccupied ? "BELEGT" : "FREI");
    Serial.print(" | CSQ: ");
    Serial.println(signalQuality);
  }
}

// ========== SERVO ==========
void raiseBarrier() {
  if (barrierIsUp) return;
  Serial.println("⬆️  Hebe Bügel...");
  barrierServo.write(SERVO_POS_UP);
  delay(SERVO_SPEED_MS);
  barrierIsUp = true;
  Serial.println("✅ Bügel oben");
}

void lowerBarrier() {
  if (!barrierIsUp) return;
  Serial.println("⬇️  Senke Bügel...");
  barrierServo.write(SERVO_POS_DOWN);
  delay(SERVO_SPEED_MS);
  barrierIsUp = false;
  Serial.println("✅ Bügel unten");
}

// ========== API: COMMANDS ==========
void pollCommands() {
  if (!gprsConnected) return;
  
  String url = String(PRODUCTION_API_BASE) + "/api/hardware/" + String(DEVICE_ID) + "/commands";
  
  Serial.println("📥 Hole Commands...");
  String response = httpGET(url.c_str());
  
  // Parse Response (einfache Parsing)
  if (response.indexOf("\"commands\"") != -1) {
    // Check for raise_barrier
    if (response.indexOf("raise_barrier") != -1) {
      Serial.println("  → raise_barrier");
      raiseBarrier();
    }
    // Check for lower_barrier
    if (response.indexOf("lower_barrier") != -1) {
      Serial.println("  → lower_barrier");
      lowerBarrier();
    }
    // Check for reset
    if (response.indexOf("\"reset\"") != -1) {
      Serial.println("  → reset");
      ESP.restart();
    }
  }
}

// ========== API: TELEMETRIE ==========
void sendTelemetry() {
  if (!gprsConnected) return;
  
  String url = String(PRODUCTION_API_BASE) + "/api/hardware/" + String(DEVICE_ID) + "/telemetry";
  
  // JSON erstellen (manuell, da ArduinoJson mit AT Commands kompliziert)
  String json = "{";
  json += "\"battery_level\":" + String(batteryVoltage, 2) + ",";
  json += "\"rssi\":" + String(signalQuality) + ",";
  json += "\"occupancy\":\"" + String(isOccupied ? "occupied" : "free") + "\",";
  json += "\"last_mag\":{\"x\":0,\"y\":0,\"z\":0}";
  json += "}";
  
  Serial.println("📤 Sende Telemetrie:");
  Serial.println("   " + json);
  
  String response = httpPOST(url.c_str(), json.c_str());
  
  if (response.indexOf("\"status\":\"ok\"") != -1 || response.indexOf("200") != -1) {
    Serial.println("✅ Telemetrie gesendet");
  } else {
    Serial.println("❌ Telemetrie-Fehler");
    Serial.println(response);
  }
}
