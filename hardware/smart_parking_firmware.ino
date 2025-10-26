/*
 * Smart Parking Hardware Controller
 * ESP32-S3 + SIM7600E + Solar Power Management
 * 
 * Features:
 * - Ultrasonic occupancy detection
 * - Electric barrier control
 * - Solar power monitoring
 * - 4G/LTE communication
 * - Deep sleep power saving
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <EEPROM.h>
#include "esp_sleep.h"
#include "driver/adc.h"

// ========== PIN DEFINITIONS ==========
// Sensors (safe GPIOs for ESP32 Dev Module)
#define ULTRASONIC_TRIG  23
#define ULTRASONIC_ECHO  22
#define LIMIT_UP         21
#define LIMIT_DOWN       5
#define MOTION_SENSOR    13

// Actuators (avoid GPIO6-11 used by SPI flash)
#define RELAY_UP        25
#define RELAY_DOWN      26
#define STATUS_LED      2

// Power monitoring
// Note: On ESP32 you should use numeric GPIOs for analogRead; A0/A1 are not defined.
#if defined(ARDUINO_ARCH_ESP32)
  // Pick two ADC-capable GPIOs that are free on your wiring. Adjust if needed.
  #define BATTERY_ADC   14
  #define SOLAR_ADC     15
#else
  #define BATTERY_ADC   A0
  #define SOLAR_ADC     A1
#endif

// Communication (use UART2: RX=16, TX=17)
#define SIM_TX         17
#define SIM_RX         16
// SIM_POWER is connected to SIM7600 PWRKEY on many breakout boards
#define SIM_POWER      19
// Optional pins: uncomment and set if available on your board
// #define SIM_PWR_EN   18   // Some boards require PWR_EN HIGH to enable module
// #define SIM_DTR      4    // Keep DTR HIGH to avoid sleep on some modules

// Allow configurable polarity/timing for PWRKEY
#ifndef SIM_PWRKEY_ACTIVE_LEVEL
#define SIM_PWRKEY_ACTIVE_LEVEL LOW   // Most SIM7600 boards: pull LOW to toggle
#endif
#ifndef SIM_PWRKEY_IDLE_LEVEL
#define SIM_PWRKEY_IDLE_LEVEL   HIGH
#endif
#ifndef SIM_PWRKEY_PULSE_MS
#define SIM_PWRKEY_PULSE_MS     2000  // 2.0s pulse (more tolerant)
#endif
#ifndef SIM_BOOT_DELAY_MS
#define SIM_BOOT_DELAY_MS       8000  // Wait after power-on
#endif

// Emergency (avoid GPIO6-11)
#define EMERGENCY_STOP  27

// ========== CONFIGURATION ==========
// Set to 1 to build a simple Serial <-> Modem bridge for wiring tests.
#ifndef DIAG_BRIDGE
#define DIAG_BRIDGE 0
#endif
const char* DEVICE_ID = "PARK_DEVICE_001";  // Unique per device
const char* API_BASE = "https://isa-collecting-stopping-husband.trycloudflare.com/api";  // Public API base (Cloudflare)
const char* APN = "data.swisscom.ch";  // SIM provider APN
// Optional SIM PIN: set if your SIM requires it, otherwise leave empty
const char* SIM_PIN = "";
// Optional APN credentials (Swisscom typically not required for consumer APN, but try username/password = "gprs" if needed)
const char* APN_USER = "";  // set to non-empty only if required
const char* APN_PASS = "";  // set to non-empty only if required

// Timing constants
const unsigned long HEARTBEAT_INTERVAL = 30000;  // 30 seconds
const unsigned long SENSOR_INTERVAL = 5000;      // 5 seconds
const unsigned long DEEP_SLEEP_TIME = 300000000; // 5 minutes in microseconds

// ========== GLOBAL VARIABLES ==========
// Use HardwareSerial on ESP32 (Serial2 for custom pins)
HardwareSerial &sim800 = Serial2;

struct DeviceState {
  bool is_occupied = false;
  bool barrier_up = false;
  float battery_level = 0.0;
  float solar_voltage = 0.0;
  int signal_strength = 0;
  float temperature = 0.0;
  unsigned long last_motion = 0;
  bool emergency_stop = false;
} state;

unsigned long last_heartbeat = 0;
unsigned long last_sensor_check = 0;
bool is_connected = false;

// Forward declaration for HTTP function (Arduino preprocessor can miss defaults)
bool sendHTTPRequest(String method, String endpoint, String payload, String* response = nullptr);

// ======== MODEM UTILS ========
static void simDrain(unsigned long ms = 50) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    while (sim800.available()) { (void)sim800.read(); }
    delay(1);
  }
}

static bool waitForToken(const char* token, unsigned long timeoutMs) {
  String buf;
  unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    while (sim800.available()) {
      char c = (char)sim800.read();
      buf += c;
      if (buf.length() > 512) buf.remove(0, buf.length() - 512);
      if (buf.indexOf(token) != -1) {
        return true;
      }
    }
    delay(1);
  }
  return false;
}

static void simPowerPulseWithLevels(int active, int idle, unsigned long pulseMs, unsigned long bootDelayMs) {
  // Many SIM7600 boards expect a PWRKEY active pulse (often LOW ~1.5s)
  Serial.println("PWRKEY pulse...");
  digitalWrite(SIM_POWER, active);
  delay(pulseMs);
  digitalWrite(SIM_POWER, idle);
  delay(bootDelayMs);
}

static void simPowerPulse() {
  simPowerPulseWithLevels(SIM_PWRKEY_ACTIVE_LEVEL, SIM_PWRKEY_IDLE_LEVEL, SIM_PWRKEY_PULSE_MS, SIM_BOOT_DELAY_MS);
}

static bool atReadyTry(unsigned long perTryMs) {
  simDrain(10);
  for (int i = 0; i < 3; ++i) {
    sim800.println("AT");
    if (waitForToken("OK", perTryMs)) return true;
  }
  return false;
}

// ========== SETUP ==========
#if !DIAG_BRIDGE
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("Smart Parking Hardware Starting...");
  
  // Initialize pins
  initializePins();
  
  // Initialize EEPROM for settings
  EEPROM.begin(512);
  
  // Initialize SIM module
  if (!initializeSIM()) {
    Serial.println("ERROR: Modem not responding. Check PWRKEY wiring/polarity and power.");
    // Blink LED fast to indicate failure
    for (int i=0;i<10;i++){ digitalWrite(STATUS_LED, HIGH); delay(150); digitalWrite(STATUS_LED, LOW); delay(150);}    
    // Skip network and continue minimal loop
  } else {
    // Connect to network
    connectToNetwork();
  }
  
  // Initialize sensors
  initializeSensors();
  
  // Read initial state
  updateSensorReadings();
  
  // Register device with server
  registerDevice();
  
  Serial.println("Setup complete. Starting main loop...");
}

// ========== MAIN LOOP ==========
void loop() {
  unsigned long now = millis();
  
  // Check emergency stop
  if (digitalRead(EMERGENCY_STOP) == LOW) {
    handleEmergencyStop();
    return;
  }
  
  // Update sensor readings
  if (now - last_sensor_check >= SENSOR_INTERVAL) {
    updateSensorReadings();
    last_sensor_check = now;
  }
  
  // Send heartbeat
  if (now - last_heartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    checkForCommands();
    last_heartbeat = now;
  }
  
  // Power management
  managePower();
  
  delay(1000);
}
#endif // !DIAG_BRIDGE

// ========== PIN INITIALIZATION ==========
void initializePins() {
  // Sensors
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);
  pinMode(LIMIT_UP, INPUT_PULLUP);
  pinMode(LIMIT_DOWN, INPUT_PULLUP);
  pinMode(MOTION_SENSOR, INPUT);
  pinMode(EMERGENCY_STOP, INPUT_PULLUP);
  
  // Actuators
  pinMode(RELAY_UP, OUTPUT);
  pinMode(RELAY_DOWN, OUTPUT);
  pinMode(STATUS_LED, OUTPUT);
  pinMode(SIM_POWER, OUTPUT);
  
  // Initial states
  digitalWrite(RELAY_UP, LOW);
  digitalWrite(RELAY_DOWN, LOW);
  digitalWrite(STATUS_LED, LOW);
  digitalWrite(SIM_POWER, SIM_PWRKEY_IDLE_LEVEL);
  
  // ADC for power monitoring
  analogReadResolution(12);
}

// ========== SIM MODULE ==========
bool initializeSIM() {
  Serial.println("Initializing SIM module...");

  // Ensure control pins are in known states
  pinMode(SIM_POWER, OUTPUT);
#ifdef SIM_PWR_EN
  pinMode(SIM_PWR_EN, OUTPUT);
  digitalWrite(SIM_PWR_EN, HIGH); // enable module
#endif
#ifdef SIM_DTR
  pinMode(SIM_DTR, OUTPUT);
  digitalWrite(SIM_DTR, HIGH); // keep awake
#endif
  digitalWrite(SIM_POWER, SIM_PWRKEY_IDLE_LEVEL);

  // Bring up UART at a default high baud first
  sim800.end();
  sim800.begin(115200, SERIAL_8N1, SIM_RX, SIM_TX);
  delay(100);

  // Power on pulse once
  // Try without pulsing first in case module is already on
  if (atReadyTry(800)) {
    Serial.println("Modem already responsive to AT");
  } else {
    // First attempt with configured polarity
    simPowerPulse();
  }

  // Optional: wait for URCs like RDY and CPIN
  Serial.println("Waiting for RDY/CPIN URCs...");
  waitForToken("RDY", 4000);
  waitForToken("+CPIN: READY", 5000);

  // Probe multiple baud rates without repulsing
  const long bauds[] = {115200, 57600, 38400, 9600};
  bool ready = false;
  for (long b : bauds) {
    Serial.print("Trying baud "); Serial.println(b);
    sim800.flush();
    sim800.end();
    sim800.begin(b, SERIAL_8N1, SIM_RX, SIM_TX);
    delay(150);
    if (atReadyTry(1200)) { ready = true; break; }
  }

  if (!ready) {
    // Fallback: try inverted polarity pulse once if still not responsive
    Serial.println("Trying inverted PWRKEY polarity...");
    simPowerPulseWithLevels(SIM_PWRKEY_IDLE_LEVEL, SIM_PWRKEY_ACTIVE_LEVEL, SIM_PWRKEY_PULSE_MS, SIM_BOOT_DELAY_MS);
    // Try baud scan again
    for (long b : bauds) {
      Serial.print("Trying baud "); Serial.println(b);
      sim800.flush();
      sim800.end();
      sim800.begin(b, SERIAL_8N1, SIM_RX, SIM_TX);
      delay(200);
      if (atReadyTry(1500)) { ready = true; break; }
    }
  }

  if (!ready) {
    // Last resort: restart UART and try again
    sim800.end();
    sim800.begin(115200, SERIAL_8N1, SIM_RX, SIM_TX);
    delay(200);
    if (!atReadyTry(2000)) {
      Serial.println("Modem not responding to AT");
      return false;
    }
  }

  // Disable echo
  sim800.println("ATE0");
  waitForToken("OK", 500);

  // Check SIM presence
  sim800.println("AT+CPIN?");
  if (!waitForToken("READY", 3000)) {
    Serial.println("SIM not ready");
  }

  // Network registration query (not strict here)
  sim800.println("AT+CREG?");
  waitForToken("OK", 1000);
  return true;
}

#if DIAG_BRIDGE
// ========== DIAGNOSTIC UART BRIDGE ==========
// Build with DIAG_BRIDGE=1 to use this instead of the normal logic.
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("DIAG: UART bridge on Serial2. Type AT and press Enter.");
  pinMode(STATUS_LED, OUTPUT);
  pinMode(SIM_POWER, OUTPUT);
  digitalWrite(SIM_POWER, SIM_PWRKEY_IDLE_LEVEL);
  sim800.begin(115200, SERIAL_8N1, SIM_RX, SIM_TX);
  delay(100);
  simPowerPulse();
}

void loop() {
  // forward PC->modem
  while (Serial.available()) {
    int c = Serial.read();
    sim800.write((uint8_t)c);
  }
  // forward modem->PC
  while (sim800.available()) {
    int c = sim800.read();
    Serial.write((uint8_t)c);
  }
  static unsigned long t = 0;
  if (millis() - t > 500) { t = millis(); digitalWrite(STATUS_LED, !digitalRead(STATUS_LED)); }
}
#endif

bool sendATCommand(String command, int timeout) {
  simDrain(5);
  sim800.println(command);
  String response;
  unsigned long start = millis();
  while (millis() - start < (unsigned long)timeout) {
    while (sim800.available()) {
      response += (char)sim800.read();
    }
    if (response.indexOf("OK") != -1 || response.indexOf("ERROR") != -1) break;
    delay(1);
  }
  Serial.println("AT Command: " + command);
  Serial.println("Response: " + response);
  return response.indexOf("OK") != -1;
}

// Send AT and capture raw response
bool sendAT(String command, String &out, int timeout) {
  simDrain(5);
  sim800.println(command);
  out = "";
  unsigned long start = millis();
  while (millis() - start < (unsigned long)timeout) {
    while (sim800.available()) {
      out += (char)sim800.read();
    }
    if (out.indexOf("OK") != -1 || out.indexOf("ERROR") != -1) break;
    delay(1);
  }
  Serial.println("AT Command: " + command);
  Serial.println("Response: " + out);
  return out.indexOf("OK") != -1;
}

static bool ensureSimReady(unsigned long timeoutMs = 20000) {
  unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    String resp;
    if (!sendAT("AT+CPIN?", resp, 3000)) { delay(1000); continue; }
    if (resp.indexOf("READY") != -1) { Serial.println("SIM READY"); return true; }
    if (resp.indexOf("SIM PIN") != -1) {
      if (String(SIM_PIN).length() > 0) {
        Serial.println("Entering SIM PIN...");
        sendATCommand("AT+CPIN=\"" + String(SIM_PIN) + "\"", 5000);
        delay(5000);
      } else {
        Serial.println("SIM needs PIN but SIM_PIN is empty");
        return false;
      }
    } else if (resp.indexOf("PUK") != -1) {
      Serial.println("SIM PUK required");
      return false;
    }
    delay(1000);
  }
  Serial.println("Timeout waiting for SIM READY");
  return false;
}

// ========== NETWORK CONNECTION ==========
void connectToNetwork() {
  Serial.println("Connecting to cellular network...");
  if (!ensureSimReady()) {
    Serial.println("SIM not ready – aborting network attach");
    return;
  }
  
  // Configure APN
  sendATCommand("AT+CGDCONT=1,\"IP\",\"" + String(APN) + "\"", 3000);
  // If username/password provided, configure PDP context authentication
  if (String(APN_USER).length() > 0 || String(APN_PASS).length() > 0) {
    // AT+CGAUTH=<cid>,<auth_type>,<user>,<pwd>
    // auth_type: 1= PAP, 2= CHAP (start with PAP; try CHAP if network rejects)
    sendATCommand("AT+CGAUTH=1,1,\"" + String(APN_USER) + "\",\"" + String(APN_PASS) + "\"", 5000);
  }
  
  // Attach to packet service
  sendATCommand("AT+CGATT=1", 10000);
  
  // Activate PDP context
  sendATCommand("AT+CGACT=1,1", 10000);
  
  // Wait for network registration
  int attempts = 0;
  is_connected = false;
  while (attempts < 30) {
    String resp;
    if (sendAT("AT+CREG?", resp, 3000)) {
      // Expect something like: +CREG: 0,1 or 0,5 when registered
      if (resp.indexOf(",1") != -1 || resp.indexOf(",5") != -1) {
        is_connected = true;
        break;
      }
    }
    delay(2000);
    attempts++;
  }
  
  if (is_connected) {
    Serial.println("Connected to cellular network");
    digitalWrite(STATUS_LED, HIGH);
  } else {
    Serial.println("Failed to connect to network");
    // Fallback: if APN credentials set, try CHAP (auth_type=2)
    if (String(APN_USER).length() > 0 || String(APN_PASS).length() > 0) {
      Serial.println("Retry with CHAP authentication...");
      // Deactivate PDP
      sendATCommand("AT+CGACT=0,1", 8000);
      // Set CHAP
      sendATCommand("AT+CGAUTH=1,2,\"" + String(APN_USER) + "\",\"" + String(APN_PASS) + "\"", 5000);
      // Reactivate PDP
      sendATCommand("AT+CGACT=1,1", 10000);
      // Check registration again (shorter loop)
      attempts = 0;
      while (attempts < 10) {
        String resp2;
        if (sendAT("AT+CREG?", resp2, 3000)) {
          if (resp2.indexOf(",1") != -1 || resp2.indexOf(",5") != -1) {
            is_connected = true;
            break;
          }
        }
        delay(2000);
        attempts++;
      }
      if (is_connected) {
        Serial.println("Connected after CHAP retry");
        digitalWrite(STATUS_LED, HIGH);
      } else {
        Serial.println("Still not connected after CHAP retry");
      }
    }
  }
}

// ========== SENSOR FUNCTIONS ==========
// On some ESP32 variants, temperatureRead() is unavailable.
// Provide a simple stub to keep builds portable.
static float getTemperature() {
  // TODO: Replace with actual temperature reading if needed
  return 25.0; // default ambient
}

void initializeSensors() {
  // Initialize ultrasonic sensor
  digitalWrite(ULTRASONIC_TRIG, LOW);
  delayMicroseconds(2);
  
  // Check initial barrier position
  state.barrier_up = digitalRead(LIMIT_UP) == LOW;
  
  Serial.println("Sensors initialized");
}

void updateSensorReadings() {
  // Read ultrasonic distance
  float distance = readUltrasonicDistance();
  
  // Determine occupancy (car typically 15-50cm from sensor)
  bool was_occupied = state.is_occupied;
  state.is_occupied = (distance > 15 && distance < 200);
  
  // Motion detection
  if (digitalRead(MOTION_SENSOR) == HIGH) {
    state.last_motion = millis();
  }
  
  // Power readings
  state.battery_level = readBatteryLevel();
  state.solar_voltage = readSolarVoltage();
  
  // Barrier position
  state.barrier_up = digitalRead(LIMIT_UP) == LOW;
  
  // Temperature (stubbed)
  state.temperature = getTemperature();
  
  // Log occupancy changes
  if (state.is_occupied != was_occupied) {
    Serial.println("Occupancy changed: " + String(state.is_occupied ? "OCCUPIED" : "FREE"));
    Serial.println("Distance: " + String(distance) + "cm");
  }
}

float readUltrasonicDistance() {
  digitalWrite(ULTRASONIC_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG, LOW);
  
  long duration = pulseIn(ULTRASONIC_ECHO, HIGH, 30000);  // 30ms timeout
  if (duration == 0) {
    return -1;  // Timeout
  }
  
  float distance = duration * 0.034 / 2;  // cm
  return distance;
}

float readBatteryLevel() {
  int raw = analogRead(BATTERY_ADC);
  float voltage = (raw / 4095.0) * 3.3 * 4;  // Voltage divider
  
  // Convert to percentage (11V = 0%, 14.4V = 100%)
  float percentage = ((voltage - 11.0) / 3.4) * 100.0;
  return constrain(percentage, 0, 100);
}

float readSolarVoltage() {
  int raw = analogRead(SOLAR_ADC);
  float voltage = (raw / 4095.0) * 3.3 * 6;  // Voltage divider
  return voltage;
}

// ========== COMMUNICATION ==========
void registerDevice() {
  if (!is_connected) return;
  
  DynamicJsonDocument doc(1024);
  doc["hardware_id"] = DEVICE_ID;
  doc["device_type"] = "smart_barrier";
  doc["firmware_version"] = "1.0.0";
  doc["spot_id"] = "SPOT_001";  // Configure per device
  
  String payload;
  serializeJson(doc, payload);
  
  if (sendHTTPRequest("POST", "/hardware/register", payload)) {
    Serial.println("Device registered successfully");
  } else {
    Serial.println("Failed to register device");
  }
}

void sendHeartbeat() {
  if (!is_connected) {
    connectToNetwork();
    return;
  }
  
  DynamicJsonDocument doc(1024);
  doc["hardware_id"] = DEVICE_ID;
  doc["is_occupied"] = state.is_occupied;
  doc["barrier_position"] = state.barrier_up ? "up" : "down";
  doc["battery_level"] = state.battery_level;
  doc["solar_voltage"] = state.solar_voltage;
  // Read actual signal strength via AT+CSQ
  {
    String csq;
    if (sendAT("AT+CSQ", csq, 1500)) {
      // +CSQ: <rssi>,<ber>
      int idx = csq.indexOf("+CSQ: ");
      if (idx != -1) {
        int comma = csq.indexOf(',', idx);
        if (comma != -1) {
          String rssiStr = csq.substring(idx + 6, comma);
          int rssiVal = rssiStr.toInt();
          // Convert 0..31 to approx dBm: dBm ~= -113 + 2*rssi (99 = unknown)
          if (rssiVal >= 0 && rssiVal <= 31) {
            state.signal_strength = -113 + 2 * rssiVal;
          }
        }
      }
    }
  }
  doc["signal_strength"] = state.signal_strength;
  doc["temperature"] = state.temperature;

  
  String payload;
  serializeJson(doc, payload);
  
  String endpoint = "/hardware/" + String(DEVICE_ID) + "/heartbeat";
  if (sendHTTPRequest("POST", endpoint, payload)) {
    Serial.println("Heartbeat sent successfully");
  } else {
    Serial.println("Failed to send heartbeat");
  }
}

void checkForCommands() {
  String endpoint = "/hardware/" + String(DEVICE_ID) + "/commands";
  String response;
  
  if (sendHTTPRequest("GET", endpoint, "", &response)) {
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, response);
    
    JsonArray commands = doc["commands"];
    for (JsonObject cmd : commands) {
      String command = cmd["command"];
      executeCommand(command, cmd["parameters"]);
    }
  }
}

void executeCommand(String command, JsonObject parameters) {
  Serial.println("Executing command: " + command);
  
  if (command == "raise_barrier") {
    raiseBarrier();
  } else if (command == "lower_barrier") {
    lowerBarrier();
  } else if (command == "reset") {
    ESP.restart();
  } else if (command == "update_settings") {
    // Update device settings
    Serial.println("Settings update requested");
  }
}

// ========== BARRIER CONTROL ==========
void raiseBarrier() {
  if (state.emergency_stop) return;
  
  Serial.println("Raising barrier...");
  
  // Stop any current movement
  digitalWrite(RELAY_UP, LOW);
  digitalWrite(RELAY_DOWN, LOW);
  delay(100);
  
  // Start raising
  digitalWrite(RELAY_UP, HIGH);
  
  // Wait for limit switch or timeout
  unsigned long start = millis();
  while (digitalRead(LIMIT_UP) == HIGH && millis() - start < 10000) {
    delay(100);
    if (digitalRead(EMERGENCY_STOP) == LOW) {
      digitalWrite(RELAY_UP, LOW);
      return;
    }
  }
  
  // Stop motor
  digitalWrite(RELAY_UP, LOW);
  state.barrier_up = digitalRead(LIMIT_UP) == LOW;
  
  Serial.println("Barrier raised: " + String(state.barrier_up));
}

void lowerBarrier() {
  if (state.emergency_stop) return;
  
  Serial.println("Lowering barrier...");
  
  // Stop any current movement
  digitalWrite(RELAY_UP, LOW);
  digitalWrite(RELAY_DOWN, LOW);
  delay(100);
  
  // Start lowering
  digitalWrite(RELAY_DOWN, HIGH);
  
  // Wait for limit switch or timeout
  unsigned long start = millis();
  while (digitalRead(LIMIT_DOWN) == HIGH && millis() - start < 10000) {
    delay(100);
    if (digitalRead(EMERGENCY_STOP) == LOW) {
      digitalWrite(RELAY_DOWN, LOW);
      return;
    }
  }
  
  // Stop motor
  digitalWrite(RELAY_DOWN, LOW);
  state.barrier_up = digitalRead(LIMIT_UP) == LOW;
  
  Serial.println("Barrier lowered: " + String(!state.barrier_up));
}

// ========== HTTP COMMUNICATION ==========
bool sendHTTPRequest(String method, String endpoint, String payload, String* response) {
  String url = String(API_BASE) + endpoint;
  bool use_https = url.startsWith("https://");
  
  // Enforce HTTPS only
  if (!use_https) {
    Serial.println("ERROR: HTTPS required. Set API_BASE to https://...");
    return false;
  }
  
  // Use AT commands for HTTP
  sim800.println("AT+HTTPINIT");
  delay(1000);
  
  sim800.println("AT+HTTPPARA=\"CID\",1");
  delay(1000);

  // Enable SSL (HTTPS-only)
  sim800.println("AT+HTTPSSL=1");
  delay(500);
  
  sim800.println("AT+HTTPPARA=\"URL\",\"" + url + "\"");
  delay(1000);
  // Allow redirects (optional)
  sim800.println("AT+HTTPPARA=\"REDIR\",1");
  delay(200);
  
  if (method == "POST" && payload.length() > 0) {
    sim800.println("AT+HTTPPARA=\"CONTENT\",\"application/json\"");
    delay(1000);
    
  sim800.println("AT+HTTPDATA=" + String(payload.length()) + ",10000");
  // Wait for DOWNLOAD prompt
  waitForToken("DOWNLOAD", 2000);
  sim800.print(payload);
  waitForToken("OK", 3000);
    
    sim800.println("AT+HTTPACTION=1");  // POST
  } else {
    sim800.println("AT+HTTPACTION=0");  // GET
  }
  
  // Wait for action URC: +HTTPACTION: <method>,<status>,<datalen>
  String actionResp;
  unsigned long start = millis();
  int statusCode = -1;
  while (millis() - start < 30000UL) {
    while (sim800.available()) {
      actionResp += (char)sim800.read();
    }
    int p = actionResp.indexOf("+HTTPACTION:");
    if (p != -1) {
      // Try to parse status code
      // Example: \r\n+HTTPACTION: 1,200,123\r\n
      int firstComma = actionResp.indexOf(',', p);
      int secondComma = firstComma != -1 ? actionResp.indexOf(',', firstComma + 1) : -1;
      if (firstComma != -1 && secondComma != -1) {
        String codeStr = actionResp.substring(firstComma + 1, secondComma);
        statusCode = codeStr.toInt();
      }
      break;
    }
    delay(10);
  }

  // Read response body (optional)
  sim800.println("AT+HTTPREAD");
  delay(500);
  String body = "";
  unsigned long rstart = millis();
  while (millis() - rstart < 5000UL) {
    while (sim800.available()) {
      body += (char)sim800.read();
    }
    if (body.indexOf("OK") != -1) break;
    delay(10);
  }
  if (response) *response = body;

  sim800.println("AT+HTTPTERM");
  delay(500);
  
  return statusCode >= 200 && statusCode < 300;
}

// ========== POWER MANAGEMENT ==========
void managePower() {
  // Enter deep sleep if battery low and no activity
  if (state.battery_level < 20 && millis() - state.last_motion > 300000) {
    Serial.println("Entering deep sleep mode...");
    esp_sleep_enable_timer_wakeup(DEEP_SLEEP_TIME);
    esp_deep_sleep_start();
  }
  
  // Reduce heartbeat frequency if battery low
  if (state.battery_level < 50) {
    // Implement reduced frequency logic
  }
}

// ========== EMERGENCY FUNCTIONS ==========
void handleEmergencyStop() {
  state.emergency_stop = true;
  
  // Stop all motors immediately
  digitalWrite(RELAY_UP, LOW);
  digitalWrite(RELAY_DOWN, LOW);
  
  // Flash status LED
  for (int i = 0; i < 10; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(100);
    digitalWrite(STATUS_LED, LOW);
    delay(100);
  }
  
  Serial.println("EMERGENCY STOP ACTIVATED");
  
  // Wait for reset
  while (digitalRead(EMERGENCY_STOP) == LOW) {
    delay(1000);
  }
  
  state.emergency_stop = false;
  Serial.println("Emergency stop released");
}
