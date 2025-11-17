/*
 * Smart Parking ESP32 + SIM7600 mit TinyGSM
 * Vereinfachte Version mit bewährter Library
 */

#define TINY_GSM_MODEM_SIM7600

#include <TinyGsmClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <Wire.h>

// ========== CONFIGURATION ==========
const char* DEVICE_ID = "PARK_DEVICE_001";
const char* API_HOST = "parking.gashis.ch";
const char* API_BASE = "";  // Empty - endpoints already include full path
const int API_PORT = 443;  // HTTPS
const char* APN = "gprs.swisscom.ch";

// ========== PINS ==========
#define SIM_TX 26  // ESP32 TX → SIM7600 RXD
#define SIM_RX 27  // ESP32 RX → SIM7600 TXD
#define SERVO_PIN 14
#define I2C_SDA 21
#define I2C_SCL 22
#define STATUS_LED 2

// ========== SERVO POSITIONS ==========
#define SERVO_POS_UP 20
#define SERVO_POS_DOWN 110

// ========== TIMING ==========
const unsigned long HEARTBEAT_INTERVAL = 30000;
const unsigned long COMMAND_POLL_INTERVAL = 10000;

// ========== GLOBALS ==========
HardwareSerial sim7600Serial(1);
TinyGsm modem(sim7600Serial);

Servo barrierServo;
bool isOccupied = false;
bool barrierIsUp = false;
unsigned long lastHeartbeat = 0;
unsigned long lastCommandPoll = 0;

// MMC5603 Magnetometer
#define MMC5603_ADDR 0x30
int16_t mag_baseline_x = 0;
int16_t mag_baseline_y = 0;
int16_t mag_baseline_z = 0;
const int MAG_THRESHOLD = 500;

// ========== MMC5603 FUNCTIONS ==========
void initMMC5603() {
  Wire.begin(I2C_SDA, I2C_SCL);
  delay(100);
  
  Wire.beginTransmission(MMC5603_ADDR);
  if (Wire.endTransmission() == 0) {
    Serial.println("✅ MMC5603 detected");
    delay(2000);
    int16_t x, y, z;
    readMagnetometer(&x, &y, &z);
    mag_baseline_x = x;
    mag_baseline_y = y;
    mag_baseline_z = z;
    Serial.printf("Baseline: X=%d, Y=%d, Z=%d\n", x, y, z);
  } else {
    Serial.println("⚠️  MMC5603 not found");
  }
}

void readMagnetometer(int16_t* x, int16_t* y, int16_t* z) {
  // Trigger measurement (TM_M bit in Control Register 0)
  Wire.beginTransmission(MMC5603_ADDR);
  Wire.write(0x1B);  // Control Register 0
  Wire.write(0x01);  // TM_M: Take measurement
  Wire.endTransmission();
  
  delay(10);  // Wait for measurement to complete
  
  // Read data from Xout0 register (0x00)
  Wire.beginTransmission(MMC5603_ADDR);
  Wire.write(0x00);
  Wire.endTransmission(false);
  Wire.requestFrom(MMC5603_ADDR, 9);  // Read 9 bytes (3 axes x 3 bytes each)
  
  if (Wire.available() >= 9) {
    // MMC5603 outputs 18-bit data (3 bytes per axis)
    uint32_t x_raw = ((uint32_t)Wire.read() << 12) | ((uint32_t)Wire.read() << 4) | ((uint32_t)Wire.read() >> 4);
    uint32_t y_raw = ((uint32_t)Wire.read() << 12) | ((uint32_t)Wire.read() << 4) | ((uint32_t)Wire.read() >> 4);
    uint32_t z_raw = ((uint32_t)Wire.read() << 12) | ((uint32_t)Wire.read() << 4) | ((uint32_t)Wire.read() >> 4);
    
    // Convert to signed 16-bit (center around 131072, scale down)
    *x = (int16_t)((x_raw - 131072) / 16);
    *y = (int16_t)((y_raw - 131072) / 16);
    *z = (int16_t)((z_raw - 131072) / 16);
  } else {
    Serial.println("⚠️  MMC5603 read failed");
    *x = *y = *z = 0;
  }
}

void updateOccupancy() {
  int16_t x, y, z;
  readMagnetometer(&x, &y, &z);
  
  int diff = abs(x - mag_baseline_x) + abs(y - mag_baseline_y) + abs(z - mag_baseline_z);
  bool wasOccupied = isOccupied;
  isOccupied = (diff > MAG_THRESHOLD);
  
  if (isOccupied != wasOccupied) {
    Serial.printf("🚗 Belegung: %s (Diff: %d)\n", isOccupied ? "BELEGT" : "FREI", diff);
  }
}

// ========== SERVO FUNCTIONS ==========
void raiseBarrier() {
  if (barrierIsUp) return;
  Serial.println("⬆️  Hebe Bügel");
  barrierServo.write(SERVO_POS_UP);
  delay(1000);
  barrierIsUp = true;
}

void lowerBarrier() {
  if (!barrierIsUp) return;
  Serial.println("⬇️  Senke Bügel");
  barrierServo.write(SERVO_POS_DOWN);
  delay(1000);
  barrierIsUp = false;
}

// ========== HTTP/HTTPS via AT Commands ==========
String sendATCommand(String cmd, unsigned long timeout = 2000) {
  sim7600Serial.println(cmd);
  String response = "";
  unsigned long start = millis();
  
  while (millis() - start < timeout) {
    while (sim7600Serial.available()) {
      char c = sim7600Serial.read();
      response += c;
    }
    if (response.indexOf("OK") != -1 || response.indexOf("ERROR") != -1) {
      break;
    }
  }
  return response;
}

String waitForHTTPResponse(unsigned long timeout = 30000) {
  // Wait specifically for +HTTPACTION response (comes async after OK)
  String response = "";
  unsigned long start = millis();
  
  while (millis() - start < timeout) {
    while (sim7600Serial.available()) {
      char c = sim7600Serial.read();
      response += c;
    }
    // +HTTPACTION: <method>,<status_code>,<data_len>
    if (response.indexOf("+HTTPACTION:") != -1) {
      // Wait a bit more for complete response
      delay(500);
      while (sim7600Serial.available()) {
        response += (char)sim7600Serial.read();
      }
      break;
    }
  }
  return response;
}

bool httpRequest(String method, String endpoint, String payload = "") {
  String url = "https://" + String(API_HOST) + String(API_BASE) + endpoint;
  Serial.println("📡 " + method + " " + url);
  
  // Terminate any previous HTTP session
  sendATCommand("AT+HTTPTERM", 1000);
  delay(500);
  
  // Initialize HTTP
  String resp = sendATCommand("AT+HTTPINIT", 2000);
  if (resp.indexOf("ERROR") != -1 && resp.indexOf("OK") == -1) {
    Serial.println("⚠️  HTTP already initialized");
  }
  
  // Set URL
  sendATCommand("AT+HTTPPARA=\"URL\",\"" + url + "\"", 2000);
  
  // Enable SSL for HTTPS
  sendATCommand("AT+HTTPSSL=1", 2000);
  
  // Set content type for POST
  if (method == "POST") {
    sendATCommand("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 2000);
    
    // Send payload
    if (payload.length() > 0) {
      resp = sendATCommand("AT+HTTPDATA=" + String(payload.length()) + ",10000", 2000);
      if (resp.indexOf("DOWNLOAD") != -1) {
        delay(100);
        sim7600Serial.print(payload);
        delay(2000);
      }
    }
  }
  
  // Execute HTTP action (0=GET, 1=POST)
  String actionCmd = (method == "POST") ? "AT+HTTPACTION=1" : "AT+HTTPACTION=0";
  sendATCommand(actionCmd, 2000);  // Just send command, get OK
  
  // Now wait for actual +HTTPACTION response
  Serial.println("⏳ Waiting for HTTP response...");
  resp = waitForHTTPResponse(30000);
  
  Serial.println("HTTP Response: " + resp);
  
  // Parse +HTTPACTION: 0,200,1234 or +HTTPACTION: 1,200,1234
  int statusStart = resp.indexOf(",");
  if (statusStart != -1) {
    statusStart++;
    int statusEnd = resp.indexOf(",", statusStart);
    if (statusEnd != -1) {
      String statusCode = resp.substring(statusStart, statusEnd);
      Serial.println("Status Code: " + statusCode);
      
      if (statusCode == "200" || statusCode == "201") {
        Serial.println("✅ HTTPS Success");
        
        // Read response body
        String readResp = sendATCommand("AT+HTTPREAD", 5000);
        
        // Terminate HTTP session
        sendATCommand("AT+HTTPTERM", 1000);
        
        return true;
      } else {
        Serial.println("❌ HTTP Error: " + statusCode);
      }
    }
  } else {
    Serial.println("⚠️  No +HTTPACTION response received");
  }
  
  // Terminate HTTP session
  sendATCommand("AT+HTTPTERM", 1000);
  
  return false;
}

void sendTelemetry() {
  DynamicJsonDocument doc(512);
  doc["battery_level"] = 3.7;
  doc["rssi"] = modem.getSignalQuality();
  doc["occupancy"] = isOccupied ? "occupied" : "free";
  
  int16_t x, y, z;
  readMagnetometer(&x, &y, &z);
  JsonObject mag = doc.createNestedObject("last_mag");
  mag["x"] = x;
  mag["y"] = y;
  mag["z"] = z;
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.println("📤 Sende Telemetrie...");
  httpRequest("POST", "/hardware/" + String(DEVICE_ID) + "/telemetry", payload);
}

void pollCommands() {
  Serial.println("📥 Hole Commands...");
  httpRequest("GET", "/hardware/" + String(DEVICE_ID) + "/commands");
}

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n==================================");
  Serial.println("Smart Parking + SIM7600 (TinyGSM)");
  Serial.println("==================================");
  
  pinMode(STATUS_LED, OUTPUT);
  
  // Init Servo
  barrierServo.attach(SERVO_PIN);
  barrierServo.write(SERVO_POS_DOWN);
  
  // Init Magnetometer
  initMMC5603();
  
  // Init SIM7600
  sim7600Serial.begin(115200, SERIAL_8N1, SIM_RX, SIM_TX);
  delay(3000);
  
  Serial.println("Init Modem...");
  
  // Test if modem is responsive (don't restart - it's already running)
  if (modem.testAT(5000)) {
    Serial.println("✅ Modem responsive");
  } else {
    Serial.println("⚠️  Modem not responding, trying restart...");
    modem.restart();
  }
  
  String modemInfo = modem.getModemInfo();
  Serial.println("Modem: " + modemInfo);
  
  // Wait for network
  Serial.println("Warte auf Netzwerk...");
  if (!modem.waitForNetwork(30000)) {
    Serial.println("❌ Network registration failed");
  } else {
    Serial.println("✅ Im Netz registriert");
    Serial.println("Signal: " + String(modem.getSignalQuality()));
  }
  
  // Connect GPRS
  Serial.println("Verbinde GPRS...");
  Serial.println("APN: " + String(APN));
  
  if (!modem.gprsConnect(APN, "", "")) {
    Serial.println("❌ GPRS connection failed");
    // Try once more
    delay(2000);
    if (!modem.gprsConnect(APN, "", "")) {
      Serial.println("❌ GPRS retry failed");
    }
  }
  
  if (modem.isGprsConnected()) {
    Serial.println("✅ GPRS verbunden");
    Serial.println("IP: " + modem.getLocalIP());
  }
  
  // Initial telemetry
  sendTelemetry();
  
  Serial.println("✅ Setup abgeschlossen");
  digitalWrite(STATUS_LED, HIGH);
}

// ========== MAIN LOOP ==========
void loop() {
  unsigned long now = millis();
  
  // Update sensors
  updateOccupancy();
  
  // Send heartbeat
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = now;
    
    if (!modem.isGprsConnected()) {
      Serial.println("⚠️  GPRS disconnected, reconnecting...");
      modem.gprsConnect(APN, "", "");
    }
    
    sendTelemetry();
  }
  
  // Poll commands
  if (now - lastCommandPoll >= COMMAND_POLL_INTERVAL) {
    lastCommandPoll = now;
    pollCommands();
  }
  
  delay(1000);
}
