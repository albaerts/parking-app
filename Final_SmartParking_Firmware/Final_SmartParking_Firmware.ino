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
#if defined(ARDUINO_ARCH_ESP32)
#if __has_include(<esp_arduino_version.h>)
#include <esp_arduino_version.h>
#define HAVE_ESP_ARDUINO_VERSION 1
#else
#define HAVE_ESP_ARDUINO_VERSION 0
#endif
#include "esp32-hal-ledc.h"
#endif
// Optional: use ESP32Servo library if available (easier portability)
#if __has_include(<ESP32Servo.h>)
#include <ESP32Servo.h>
#define HAVE_ESP32SERVO 1
#else
#define HAVE_ESP32SERVO 0
#endif

// (Optional magnetometer support was removed per user request)

// ========== PIN DEFINITIONS ==========
// Sensors (safe GPIOs for ESP32 Dev Module)
#define ULTRASONIC_TRIG  23
#define ULTRASONIC_ECHO  22
#define LIMIT_UP         21
#define LIMIT_DOWN       5
#define MOTION_SENSOR    13
// Hall sensor (A3144E) signal pin (active LOW with pull-up)
#define HALL_SENSOR      32

// Actuators (avoid GPIO6-11 used by SPI flash)
#define RELAY_UP        25
// Moved RELAY_DOWN off GPIO26 to avoid conflict with SIM_TX (GPIO26)
#define RELAY_DOWN      17
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

// Communication (use UART2). Your wiring:
//   SIM TXD -> ESP32 GPIO27 (so ESP32 RX=27)
//   SIM RXD -> ESP32 GPIO26 (so ESP32 TX=26)
#define SIM_TX         26
#define SIM_RX         27
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
#define SIM_PWRKEY_PULSE_MS     2500  // 2.5s pulse for more boards
#endif
#ifndef SIM_BOOT_DELAY_MS
#define SIM_BOOT_DELAY_MS       10000  // Give modem more time to boot
#endif

// Emergency (avoid GPIO6-11). IMPORTANT: Do NOT share with modem UART pins.
// Moved from 27 (SIM RX) to 16 to avoid UART conflict that can corrupt modem comms.
#define EMERGENCY_STOP  16

// ========== CONFIGURATION ==========
// Set to 1 to build a simple Serial <-> Modem bridge for wiring tests.
#ifndef DIAG_BRIDGE
#define DIAG_BRIDGE 0
#endif
// Set to 1 for detailed modem logs, 0 for quieter runtime
#ifndef VERBOSE_LOG
#define VERBOSE_LOG 1
#endif
// Use a hobby servo instead of DC motor relays
#ifndef USE_SERVO
#define USE_SERVO 1
#endif
// If not building for ESP32 and ESP32Servo lib is not available, disable servo to avoid LEDC errors
#if !defined(ARDUINO_ARCH_ESP32) && !(HAVE_ESP32SERVO)
#undef USE_SERVO
#define USE_SERVO 0
#endif
// (Optional magnetometer feature flag removed per user request)
// Detect ESP32 Arduino core major version to select LEDC API (v2 vs v3)
#if defined(ARDUINO_ARCH_ESP32)
  #if (HAVE_ESP_ARDUINO_VERSION) && defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    #define ESP32_USE_LEDC_V3_API 1
  #else
    #define ESP32_USE_LEDC_V3_API 0
  #endif
#endif
// Servo configuration (active when USE_SERVO==1)
#define SERVO_PIN           21
#define SERVO_CHANNEL       4
#define SERVO_FREQ_HZ       50
#define SERVO_RES_BITS      16
#define SERVO_MIN_US        1000
#define SERVO_MAX_US        2000
// Positions for barrier
#define SERVO_POS_DOWN_US   1000
#define SERVO_POS_UP_US     2000
#define SERVO_MOVE_DELAY_MS 900
// If the ESP32Servo lib is present, we'll use it. Otherwise, we fall back to LEDC.
#if USE_SERVO && HAVE_ESP32SERVO
static Servo barrierServo;
#endif
// Track current servo pin at runtime and driver used (for diagnostics)
static int g_servoPin = SERVO_PIN;
static const char* g_servoDriver = "none";
// Sanfter Servomodus für USB-Tests (ohne Pololu): bewegt in kleinen Schritten, um Stromspitzen zu reduzieren
static bool g_gentleServo = false;
// Letzte bekannte Servoposition in µs (für sanfte Rampen)
static int g_servoCurrentUs = -1;
// Warn if a common config mistake occurs: SIM power enable uses same pin as servo
#if defined(SIM_PWR_EN)
#if (SIM_PWR_EN == SERVO_PIN)
#warning SIM_PWR_EN equals SERVO_PIN. This will cause a conflict and the servo will not move.
#endif
#endif
// Runtime-configurable flags/values (persisted in EEPROM)
static bool g_verbose = (VERBOSE_LOG != 0);
static uint16_t servoPosUpUs = SERVO_POS_UP_US;
static uint16_t servoPosDownUs = SERVO_POS_DOWN_US;
static uint16_t servoMoveDelayMs = SERVO_MOVE_DELAY_MS;
// Modem optional deaktivieren (USB-Testmodus ohne Pololu)
#ifndef TEST_NO_MODEM
#define TEST_NO_MODEM 0
#endif
static bool g_disableModem = (TEST_NO_MODEM != 0);

// ===== EEPROM settings =====
struct PersistedSettings {
  uint32_t magic;          // magic to validate content
  uint8_t version;         // structure version
  uint8_t reserved0;       // alignment
  uint8_t verbose;         // 0/1
  uint8_t reserved1;       // alignment
  uint16_t servoUpUs;      // microseconds
  uint16_t servoDownUs;    // microseconds
  uint16_t servoDelayMs;   // milliseconds
};

static const uint32_t SETTINGS_MAGIC = 0x5350524B; // 'SPRK'
static const uint8_t SETTINGS_VERSION = 1;
static const int SETTINGS_ADDR = 0; // start of EEPROM

static void saveSettingsToEEPROM() {
  PersistedSettings ps{};
  ps.magic = SETTINGS_MAGIC;
  ps.version = SETTINGS_VERSION;
  ps.verbose = g_verbose ? 1 : 0;
  ps.servoUpUs = servoPosUpUs;
  ps.servoDownUs = servoPosDownUs;
  ps.servoDelayMs = servoMoveDelayMs;
  EEPROM.put(SETTINGS_ADDR, ps);
  EEPROM.commit();
  if (g_verbose) Serial.println("Settings saved to EEPROM");
}

static void loadSettingsFromEEPROM() {
  PersistedSettings ps{};
  EEPROM.get(SETTINGS_ADDR, ps);
  if (ps.magic == SETTINGS_MAGIC && ps.version == SETTINGS_VERSION) {
    g_verbose = (ps.verbose != 0);
    // sanity/clamp ranges
    servoPosUpUs = constrain((int)ps.servoUpUs, 500, 2500);
    servoPosDownUs = constrain((int)ps.servoDownUs, 500, 2500);
    servoMoveDelayMs = constrain((int)ps.servoDelayMs, 100, 5000);
    if (g_verbose) {
      Serial.println("Loaded settings from EEPROM:");
      Serial.print("  verbose="); Serial.println(g_verbose);
      Serial.print("  servoUpUs="); Serial.println(servoPosUpUs);
      Serial.print("  servoDownUs="); Serial.println(servoPosDownUs);
      Serial.print("  servoDelayMs="); Serial.println(servoMoveDelayMs);
    }
  } else {
    // keep defaults and persist them for next boot
    if (g_verbose) Serial.println("EEPROM settings not found; writing defaults...");
    saveSettingsToEEPROM();
  }
}
const char* DEVICE_ID = "PARK_DEVICE_001";  // Unique per device
// Target your stable production API domain (Cloudflare/HTTPS)
const char* API_BASE = "https://api.gashis.ch/api";  // Public API base
const char* APN = "data.swisscom.ch";  // SIM provider APN
// Optional SIM PIN: SIM PIN is disabled on your SIM, keep empty
const char* SIM_PIN = "";  // "" = no auto CPIN; set if SIM requires PIN
// Optional APN credentials: Swisscom consumer APN usually does NOT need auth
const char* APN_USER = "";  // set to non-empty only if required
const char* APN_PASS = "";  // set to non-empty only if required

// Timing constants
const unsigned long HEARTBEAT_INTERVAL = 30000;  // 30 seconds
const unsigned long SENSOR_INTERVAL = 5000;      // 5 seconds
const unsigned long DEEP_SLEEP_TIME = 300000000; // 5 minutes in microseconds

// ========== GLOBAL VARIABLES ==========
// Use HardwareSerial on ESP32 (Serial2 for custom pins)
HardwareSerial &sim800 = Serial2;
// Runtime-modifiable UART pins (initialized from macros above)
static int UART_RX_PIN = SIM_RX;
static int UART_TX_PIN = SIM_TX;

struct DeviceState {
  bool is_occupied = false;
  bool barrier_up = false;
  float battery_level = 0.0;
  float solar_voltage = 0.0;
  int signal_strength = 0;
  float temperature = 0.0;
  unsigned long last_motion = 0;
  bool emergency_stop = false;
  bool hall_detected = false; // true when magnet present (active LOW)
} state;

unsigned long last_heartbeat = 0;
unsigned long last_sensor_check = 0;
bool is_connected = false;
// Registration tracking
static bool device_registered = false;
static unsigned long last_register_try = 0;
const unsigned long REGISTER_RETRY_INTERVAL = 60000; // 60s between retries

// Forward declaration for HTTP function (Arduino preprocessor can miss defaults)
bool sendHTTPRequest(String method, String endpoint, String payload, String* response = nullptr);
// Forward decl for reading signal strength
int readSignalStrengthDbm();

// Explicit forward declarations (avoid Arduino auto-prototype pitfalls)
static void handleSerialCommands();
void initializePins();
void initializeSIM();
void connectToNetwork();
void initializeSensors();
void updateSensorReadings();
void registerDevice();
void sendHeartbeat();
void checkForCommands();
void managePower();
void handleEmergencyStop();
void raiseBarrier();
void lowerBarrier();
float readUltrasonicDistance();
float readBatteryLevel();
float readSolarVoltage();
bool sendAT(String command, String &out, int timeout);
bool sendATCommand(String command, int timeout);
bool ensureSimReady(unsigned long timeoutMs = 20000);
static bool setupAPNContext(const char* apn);
static bool isRegistered(unsigned long timeoutMs = 15000);
static bool hasIP();

#if USE_SERVO
// Helper: direkte Pulsweite schreiben (beachtet ESP32Servo/LEDC und g_servoPin)
static void writeServoUs(int us) {
  int clamped = constrain(us, SERVO_MIN_US, SERVO_MAX_US);
  #if HAVE_ESP32SERVO
    barrierServo.writeMicroseconds(clamped);
  #else
    #if defined(ARDUINO_ARCH_ESP32)
      int duty = (int)((float)clamped / 20000.0f * ((1 << SERVO_RES_BITS) - 1));
      #if ESP32_USE_LEDC_V3_API
        ledcWrite(g_servoPin, duty);
      #else
        ledcWrite(SERVO_CHANNEL, duty);
      #endif
    #endif
  #endif
  g_servoCurrentUs = clamped;
}

// Helper: sanftes Bewegen (kleine Schritte), reduziert Stromspitzen für USB‑Tests
static void moveServoToUs(int targetUs) {
  int target = constrain(targetUs, SERVO_MIN_US, SERVO_MAX_US);
  if (!g_gentleServo || g_servoCurrentUs < 0) {
    writeServoUs(target);
    return;
  }
  int current = g_servoCurrentUs;
  int step = (target > current) ? 20 : -20; // 20 µs Schritte
  for (int us = current; (step > 0) ? (us < target) : (us > target); us += step) {
    writeServoUs(us);
    delay(8); // ~8ms Zwischenstopp
  }
  writeServoUs(target);
}
#endif

// (Optional magnetometer state removed per user request)

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

static void simPowerPulse() {
  // Many SIM7600 boards expect a PWRKEY active pulse (often LOW ~1.5s)
  Serial.println("PWRKEY pulse...");
  digitalWrite(SIM_POWER, SIM_PWRKEY_ACTIVE_LEVEL);
  delay(SIM_PWRKEY_PULSE_MS);
  digitalWrite(SIM_POWER, SIM_PWRKEY_IDLE_LEVEL);
  delay(SIM_BOOT_DELAY_MS);
}

static void simPowerPulseInverted() {
  // Fallback pulse with inverted polarity in case the board uses opposite logic
  Serial.println("PWRKEY pulse (inverted)...");
  digitalWrite(SIM_POWER, !SIM_PWRKEY_ACTIVE_LEVEL);
  delay(SIM_PWRKEY_PULSE_MS);
  digitalWrite(SIM_POWER, !SIM_PWRKEY_IDLE_LEVEL);
  delay(SIM_BOOT_DELAY_MS);
}

// Optional: try a PWRKEY pulse on an alternate pin (e.g., GPIO4) in case wiring uses another GPIO
static void simPowerPulseOnAltPin(int altPin, bool inverted = false) {
  Serial.print("PWRKEY pulse on alt pin "); Serial.print(altPin); Serial.println(inverted ? " (inverted)" : "");
  pinMode(altPin, OUTPUT);
  if (!inverted) {
    digitalWrite(altPin, SIM_PWRKEY_ACTIVE_LEVEL);
    delay(SIM_PWRKEY_PULSE_MS);
    digitalWrite(altPin, SIM_PWRKEY_IDLE_LEVEL);
  } else {
    digitalWrite(altPin, !SIM_PWRKEY_ACTIVE_LEVEL);
    delay(SIM_PWRKEY_PULSE_MS);
    digitalWrite(altPin, !SIM_PWRKEY_IDLE_LEVEL);
  }
  delay(SIM_BOOT_DELAY_MS);
}

static bool atReadyTry(unsigned long perTryMs) {
  simDrain(10);
  for (int i = 0; i < 8; ++i) {
    sim800.println("AT");
    if (waitForToken("OK", perTryMs)) return true;
  }
  return false;
}

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("Smart Parking Hardware Starting...");
  
  // Initialize EEPROM for settings
  EEPROM.begin(512);
  loadSettingsFromEEPROM();

  // Initialize pins (uses loaded settings for servo positions)
  initializePins();
  
  // Initialize SIM module (überspringen, wenn Modem deaktiviert ist – USB-Test ohne Pololu)
  if (!g_disableModem) {
    initializeSIM();
    // Connect to network
    connectToNetwork();
  } else {
    Serial.println("Modem ist DEAKTIVIERT (USB-Testmodus). Netzwerk wird übersprungen.");
  }
  
  // Initialize sensors
  initializeSensors();
  
  // Read initial state
  updateSensorReadings();
  
  // Register device with server
  if (!g_disableModem) {
    registerDevice();
  }
  
  Serial.println("Setup complete. Starting main loop...");
}

// ========== MAIN LOOP ==========
void loop() {
  unsigned long now = millis();
  // Allow local control via Serial (type 'help' for commands)
  handleSerialCommands();
  
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
  
  // Send heartbeat (überspringen, wenn Modem deaktiviert)
  if (!g_disableModem) {
    if (now - last_heartbeat >= HEARTBEAT_INTERVAL) {
      // Retry registration periodically if not yet successful
      if (!device_registered && (now - last_register_try >= REGISTER_RETRY_INTERVAL)) {
        registerDevice();
      }
      sendHeartbeat();
      checkForCommands();
      last_heartbeat = now;
    }
  }
  
  // Power management
  managePower();
  
  delay(1000);
}

// ========== LOCAL SERIAL COMMANDS ==========
// Simple REPL to control the device from Serial Monitor (115200 baud)
// Commands:
//   up | raise | r           -> raise barrier (servo up)
//   down | lower | d         -> lower barrier (servo down)
//   mid | m                  -> move servo to 1500us (test)
//   sweep | sw               -> sweep servo between min/max a few times (diagnostics)
//   at <CMD>                 -> send raw AT command to modem (e.g., at+cpin?)
//   sim pulse|invert|test    -> pulse PWRKEY, pulse inverted, or run basic ATI/CPIN test
//   status                   -> print state and servo config
//   verbose on|off [persist] -> toggle logging, optionally persist (default persist)
//   servo up=<us> down=<us> delay=<ms> [persist=0|1]
//                             -> set servo positions and move delay; optionally persist
//   servo pin=<gpio> [test]   -> reattach servo signal to another GPIO at runtime; optional sweep test
//   help | ?                 -> show help
static void handleSerialCommands() {
  static String line;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c != '\n') {
      if (line.length() < 240) line += c;
      continue;
    }
    // process line on newline
    String raw = line;
    line = "";
    raw.trim();
    if (raw.length() == 0) return;
    String lc = raw; lc.toLowerCase();

    auto printHelp = [](){
      Serial.println("Commands:");
      Serial.println("  up | raise | r");
      Serial.println("  down | lower | d");
      Serial.println("  mid | m                 -> move servo to 1500us (test)");
      Serial.println("  sweep | sw              -> sweep between 1000-2000us (diagnostics)");
      Serial.println("  at <CMD>                -> send raw AT to modem, show response");
      Serial.println("  sim pulse|invert|test   -> PWRKEY pulse / inverted / basic ATI+CPIN test");
      Serial.println("  status");
      Serial.println("  verbose on|off [persist]");
      Serial.println("  servo up=<us> down=<us> delay=<ms> [persist=0|1] goto=<us>");
      Serial.println("  servo pin=<gpio> [test]");
    };

    if (lc == "up" || lc == "raise" || lc == "r") {
      raiseBarrier();
      return;
    }
    if (lc == "down" || lc == "lower" || lc == "d") {
      lowerBarrier();
      return;
    }
    if (lc == "status") {
      Serial.println("=== STATUS ===");
      Serial.print("barrier_up: "); Serial.println(state.barrier_up ? "true" : "false");
      Serial.print("verbose: "); Serial.println(g_verbose ? "ON" : "OFF");
      Serial.print("servo gentle: "); Serial.println(g_gentleServo ? "ON" : "OFF");
      Serial.print("servo up(us): "); Serial.println(servoPosUpUs);
      Serial.print("servo down(us): "); Serial.println(servoPosDownUs);
      Serial.print("servo delay(ms): "); Serial.println(servoMoveDelayMs);
      Serial.print("servo pin: "); Serial.println(g_servoPin);
      Serial.print("servo driver: "); Serial.println(g_servoDriver);
      Serial.print("modem: "); Serial.println(g_disableModem ? "DISABLED" : (is_connected ? "CONNECTED" : "NOT CONNECTED"));
      Serial.print("EMERGENCY_STOP pin: "); Serial.println(digitalRead(EMERGENCY_STOP) == LOW ? "LOW (ACTIVE)" : "HIGH (OK)");
      Serial.print("HALL pin: "); Serial.println(digitalRead(HALL_SENSOR) == LOW ? "LOW (MAGNET)" : "HIGH (NO MAGNET)");
      return;
    }
    if (lc == "mid" || lc == "m") {
#if USE_SERVO
  #if HAVE_ESP32SERVO
      barrierServo.writeMicroseconds((SERVO_MIN_US + SERVO_MAX_US) / 2);
      moveServoToUs((SERVO_MIN_US + SERVO_MAX_US) / 2);
  #else
    #if defined(ARDUINO_ARCH_ESP32)
      moveServoToUs((SERVO_MIN_US + SERVO_MAX_US) / 2);
    #endif
  #endif
      Serial.println("Moved servo to MID (1500us)");
#else
      Serial.println("Servo disabled in build");
#endif
      return;
    }
    if (lc == "sweep" || lc == "sw") {
#if USE_SERVO
      Serial.println("Sweeping servo between 1000us and 2000us...");
      for (int rep = 0; rep < 3; ++rep) {
        // Down (1000us)
  #if HAVE_ESP32SERVO
        barrierServo.writeMicroseconds(1000);
        moveServoToUs(1000);
  #else
    #if defined(ARDUINO_ARCH_ESP32)
        moveServoToUs(1000);
    #endif
  #endif
        delay(700);
        // Up (2000us)
  #if HAVE_ESP32SERVO
        moveServoToUs(2000);
  #else
    #if defined(ARDUINO_ARCH_ESP32)
        moveServoToUs(2000);
    #endif
  #endif
        delay(700);
      }
      Serial.println("Sweep finished.");
#else
      Serial.println("Servo disabled in build");
#endif
      return;
    }
    if (lc.startsWith("at ")) {
      // Send raw AT command to modem and print response for 2 seconds
      String cmd = raw.substring(3);
      cmd.trim();
      if (cmd.length() == 0) { Serial.println("Usage: at <CMD>"); return; }
      simDrain(10);
      sim800.println(cmd);
      unsigned long start = millis();
      String resp;
      while (millis() - start < 2000) {
        while (sim800.available()) resp += (char)sim800.read();
        delay(5);
      }
      Serial.println("--- AT RESP START ---");
      Serial.println(resp);
      Serial.println("--- AT RESP END ---");
      return;
    }
    if (lc == "sim pulse" || lc == "sim invert" || lc == "sim test") {
      if (lc == "sim pulse") { simPowerPulse(); Serial.println("PWRKEY pulse sent."); return; }
      if (lc == "sim invert") { simPowerPulseInverted(); Serial.println("PWRKEY inverted pulse sent."); return; }
      // Basic test: ATI and CPIN?
      Serial.println("Modem test: ATI / CPIN?");
      String out;
      (void)sendAT("ATI", out, 2000);
      Serial.print("ATI -> "); Serial.println(out);
      out = "";
      (void)sendAT("AT+CPIN?", out, 2000);
      Serial.print("AT+CPIN? -> "); Serial.println(out);
      return;
    }
    if (lc.startsWith("verbose ")) {
      bool persist = true;
      bool on = (lc.indexOf("on") != -1);
      bool off = (lc.indexOf("off") != -1);
      if (on == off) {
        Serial.println("Usage: verbose on|off [persist]");
        return;
      }
      // check optional 'persist' literal
      if (lc.indexOf(" persist") != -1 || lc.endsWith(" persist")) persist = true;
      g_verbose = on;
      if (persist) saveSettingsToEEPROM();
      Serial.print("Verbose set to "); Serial.println(g_verbose ? "ON" : "OFF");
      return;
    }
    if (lc.startsWith("servo ")) {
      // Parse key=value tokens
      uint16_t up = servoPosUpUs;
      uint16_t down = servoPosDownUs;
      uint16_t dly = servoMoveDelayMs;
      int gotoUs = -1; // optional immediate move target
      bool persist = true;
      // crude parsing: look for substrings
      int p;
      p = lc.indexOf("up="); if (p != -1) { int v = raw.substring(p+3).toInt(); if (v>0) up = constrain(v, 500, 2500); }
      p = lc.indexOf("down="); if (p != -1) { int v = raw.substring(p+5).toInt(); if (v>0) down = constrain(v, 500, 2500); }
      p = lc.indexOf("delay="); if (p != -1) { int v = raw.substring(p+6).toInt(); if (v>0) dly = constrain(v, 100, 5000); }
      p = lc.indexOf("goto="); if (p != -1) { int v = raw.substring(p+5).toInt(); if (v>0) gotoUs = constrain(v, 500, 2500); }
      p = lc.indexOf("persist="); if (p != -1) { int v = raw.substring(p+8).toInt(); persist = (v != 0); }
      // Handle pin change early: "servo pin=<gpio> [test]"
      int pPin = lc.indexOf("pin=");
      bool doTestAfter = (lc.indexOf(" test") != -1);
      if (pPin != -1) {
        int newPin = raw.substring(pPin+4).toInt();
        if (newPin <= 0) { Serial.println("Invalid pin value"); return; }
#if USE_SERVO
  #if HAVE_ESP32SERVO
        barrierServo.detach();
        barrierServo.setPeriodHertz(SERVO_FREQ_HZ);
        barrierServo.attach(newPin, SERVO_MIN_US, SERVO_MAX_US);
        barrierServo.writeMicroseconds(servoPosDownUs);
        g_servoPin = newPin;
        Serial.print("Servo reattached on pin "); Serial.println(g_servoPin);
        if (doTestAfter) {
          barrierServo.writeMicroseconds(1000); delay(600);
          barrierServo.writeMicroseconds(2000); delay(600);
          barrierServo.writeMicroseconds(1500);
          Serial.println("Servo pin test done (ESP32Servo)");
        }
        return;
  #else
    #if defined(ARDUINO_ARCH_ESP32)
        // LEDC path
      #if ESP32_USE_LEDC_V3_API
        // Detach old pin, attach new
        ledcDetach(g_servoPin);
        ledcAttach(newPin, SERVO_FREQ_HZ, SERVO_RES_BITS);
      #else
        // v2 API: detach old and attach new to fixed channel
        ledcDetachPin(g_servoPin);
        ledcAttachPin(newPin, SERVO_CHANNEL);
        ledcSetup(SERVO_CHANNEL, SERVO_FREQ_HZ, SERVO_RES_BITS);
      #endif
        g_servoPin = newPin;
        // Move to current down position on new pin
        {
          int duty = (int)((float)servoPosDownUs / 20000.0f * ((1 << SERVO_RES_BITS) - 1));
        #if ESP32_USE_LEDC_V3_API
          ledcWrite(g_servoPin, duty);
        #else
          ledcWrite(SERVO_CHANNEL, duty);
        #endif
        }
        Serial.print("Servo reattached on pin "); Serial.println(g_servoPin);
        if (doTestAfter) {
          int d1 = (int)((float)1000 / 20000.0f * ((1 << SERVO_RES_BITS) - 1));
          int d2 = (int)((float)2000 / 20000.0f * ((1 << SERVO_RES_BITS) - 1));
        #if ESP32_USE_LEDC_V3_API
          ledcWrite(g_servoPin, d1); delay(600);
          ledcWrite(g_servoPin, d2); delay(600);
          ledcWrite(g_servoPin, (d1+d2)/2);
        #else
          ledcWrite(SERVO_CHANNEL, d1); delay(600);
          ledcWrite(SERVO_CHANNEL, d2); delay(600);
          ledcWrite(SERVO_CHANNEL, (d1+d2)/2);
        #endif
          Serial.println("Servo pin test done (LEDC)");
        }
        return;
    #endif
  #endif
#else
        Serial.println("Servo disabled in build");
        return;
#endif
      }
      servoPosUpUs = up;
      servoPosDownUs = down;
      servoMoveDelayMs = dly;
      if (persist) saveSettingsToEEPROM();
      Serial.print("Servo updated: up="); Serial.print(servoPosUpUs);
      Serial.print(" us, down="); Serial.print(servoPosDownUs);
      Serial.print(" us, delay="); Serial.print(servoMoveDelayMs); Serial.println(" ms");
      if (gotoUs > 0) {
#if USE_SERVO
        moveServoToUs(gotoUs);
        Serial.print("Moved servo to "); Serial.print(gotoUs); Serial.println(" us");
#endif
      }
      return;
    }
    if (lc.startsWith("servo gentle ")) {
      bool on = (lc.indexOf("on") != -1);
      bool off = (lc.indexOf("off") != -1);
      if (on == off) { Serial.println("Usage: servo gentle on|off"); return; }
      g_gentleServo = on;
      Serial.print("Servo gentle mode: "); Serial.println(g_gentleServo ? "ON" : "OFF");
      return;
    }
    if (lc == "modem off" || lc == "modem on") {
      g_disableModem = (lc.endsWith("off"));
      Serial.print("Modem now "); Serial.println(g_disableModem ? "DISABLED" : "ENABLED");
      return;
    }
    if (lc == "help" || lc == "?") {
      printHelp();
      return;
    }
    Serial.println("Unknown command. Type 'help'.");
  }
}

// ========== PIN INITIALIZATION ==========
void initializePins() {
  // Sensors
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);
  // Limit-Schalter nur verwenden, wenn kein Servo eingesetzt wird
  #if !USE_SERVO
  pinMode(LIMIT_UP, INPUT_PULLUP);
  #endif
  pinMode(LIMIT_DOWN, INPUT_PULLUP);
  pinMode(MOTION_SENSOR, INPUT);
  // Hall sensor input (A3144E): active LOW when magnet present
  // Default to INPUT_PULLUP (works with open-collector output and 3.3V pull-up)
  // NOTE: If your module has a 5V pull-up on board, ensure level shifting or 3.3V operation.
  pinMode(HALL_SENSOR, INPUT_PULLUP);
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

#if USE_SERVO
  // Prefer ESP32Servo library when available
#if HAVE_ESP32SERVO
  Serial.println("Servo init: using ESP32Servo library");
  barrierServo.setPeriodHertz(SERVO_FREQ_HZ);
  barrierServo.attach(g_servoPin, SERVO_MIN_US, SERVO_MAX_US);
  barrierServo.writeMicroseconds(servoPosDownUs);
  g_servoDriver = "ESP32Servo";
  g_servoCurrentUs = servoPosDownUs;
#else
#if defined(ARDUINO_ARCH_ESP32)
  // Setup LEDC PWM for servo on GPIO18
  #if ESP32_USE_LEDC_V3_API
    Serial.println("Servo init: using LEDC v3 API");
  #else
    Serial.println("Servo init: using LEDC v2 API");
  #endif
  #if ESP32_USE_LEDC_V3_API
    // Arduino-ESP32 v3 API: attach by pin with freq and resolution
    ledcAttach(g_servoPin, SERVO_FREQ_HZ, SERVO_RES_BITS);
  #else
    // Arduino-ESP32 v2 API: setup timer/channel and attach pin to channel
    ledcSetup(SERVO_CHANNEL, SERVO_FREQ_HZ, SERVO_RES_BITS);
    ledcAttachPin(g_servoPin, SERVO_CHANNEL);
  #endif
  // Initialize to a safe position (down)
  {
    int duty = (int)((float)servoPosDownUs / 20000.0f * ((1 << SERVO_RES_BITS) - 1));
    #if ESP32_USE_LEDC_V3_API
      ledcWrite(g_servoPin, duty);
    #else
      ledcWrite(SERVO_CHANNEL, duty);
    #endif
  }
  g_servoDriver = ESP32_USE_LEDC_V3_API ? "LEDC v3" : "LEDC v2";
  g_servoCurrentUs = servoPosDownUs;
#else
  #warning Servo disabled: not ESP32 and ESP32Servo not available.
#endif
#endif
#endif
  
  // ADC for power monitoring
  analogReadResolution(12);
}

// ========== SIM MODULE ==========
void initializeSIM() {
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
  sim800.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  delay(100);

  // Power on pulse once
  simPowerPulse();

  // Optional: wait for URCs like RDY and CPIN
  Serial.println("Waiting for RDY/CPIN URCs...");
  waitForToken("RDY", 2000);
  waitForToken("+CPIN: READY", 3000);

  // Probe multiple baud rates without re-pulsing
  const long bauds[] = {115200, 57600, 38400, 9600};
  bool ready = false;
  for (long b : bauds) {
    Serial.print("Trying baud "); Serial.print(b); Serial.print(" on RX="); Serial.print(UART_RX_PIN); Serial.print(" TX="); Serial.println(UART_TX_PIN);
    sim800.flush();
    sim800.end();
    sim800.begin(b, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
    delay(150);
    if (atReadyTry(1200)) { ready = true; break; }
  }

  if (!ready) {
    // Try inverted PWRKEY polarity in case hardware expects opposite level
    Serial.println("Modem did not respond. Trying inverted PWRKEY polarity...");
    simPowerPulseInverted();
    for (long b : bauds) {
      Serial.print("Retry baud "); Serial.print(b); Serial.print(" on RX="); Serial.print(UART_RX_PIN); Serial.print(" TX="); Serial.println(UART_TX_PIN);
      sim800.flush();
      sim800.end();
      sim800.begin(b, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
      delay(200);
      if (atReadyTry(1500)) { ready = true; break; }
    }
  }

  // If still not ready, try a few likely TX pins with fixed RX
  if (!ready) {
    const int txCandidates[] = {UART_TX_PIN, 17, 26, 25};
    for (unsigned i = 0; i < sizeof(txCandidates)/sizeof(txCandidates[0]) && !ready; ++i) {
      int candTX = txCandidates[i];
      if (candTX == UART_RX_PIN) continue; // avoid same pin
      Serial.print("Trying TX candidate "); Serial.println(candTX);
      for (long b : bauds) {
        Serial.print("Retry baud "); Serial.print(b); Serial.print(" on RX="); Serial.print(UART_RX_PIN); Serial.print(" TX="); Serial.println(candTX);
        sim800.flush();
        sim800.end();
        sim800.begin(b, SERIAL_8N1, UART_RX_PIN, candTX);
        delay(200);
        if (atReadyTry(1500)) { ready = true; UART_TX_PIN = candTX; break; }
      }
    }
  }

  if (!ready) {
    // Try alternate PWRKEY pin commonly used on some boards (GPIO4)
    Serial.println("Still no AT. Trying alt PWRKEY on GPIO4...");
    simPowerPulseOnAltPin(4, false);
    for (long b : bauds) {
      Serial.print("Retry baud "); Serial.print(b); Serial.print(" on RX="); Serial.print(UART_RX_PIN); Serial.print(" TX="); Serial.println(UART_TX_PIN);
      sim800.flush();
      sim800.end();
      sim800.begin(b, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
      delay(200);
      if (atReadyTry(1500)) { ready = true; break; }
    }
  }

  if (!ready) {
    Serial.println("Trying alt PWRKEY on GPIO4 (inverted)...");
    simPowerPulseOnAltPin(4, true);
    for (long b : bauds) {
      Serial.print("Retry baud "); Serial.print(b); Serial.print(" on RX="); Serial.print(UART_RX_PIN); Serial.print(" TX="); Serial.println(UART_TX_PIN);
      sim800.flush();
      sim800.end();
      sim800.begin(b, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
      delay(200);
      if (atReadyTry(1500)) { ready = true; break; }
    }
  }

  if (!ready) {
    // Last resort: restart UART and try again a final time at 115200
    sim800.end();
  sim800.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
    delay(200);
    if (!atReadyTry(2000)) {
      Serial.println("Modem not responding to AT");
      return;
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
  if (g_verbose) {
    Serial.println("AT Command: " + command);
    Serial.println("Response: " + response);
  }
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
  if (g_verbose) {
    Serial.println("AT Command: " + command);
    Serial.println("Response: " + out);
  }
  return out.indexOf("OK") != -1;
}

// Check if the modem is registered to the network (+CREG: 0,1 or 0,5)
static bool isRegistered(unsigned long timeoutMs) {
  unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    String resp;
    if (sendAT("AT+CREG?", resp, 2000)) {
      if ((resp.indexOf(",1") != -1) || (resp.indexOf(",5") != -1)) {
        return true;
      }
    }
    delay(1000);
  }
  return false;
}

// Verify that PDP context has an IP assigned
static bool hasIP() {
  String resp;
  if (!sendAT("AT+CGPADDR=1", resp, 2000)) return false;
  // Expect something like: +CGPADDR: 1,\"10.XXX.XXX.XXX\"
  if (resp.indexOf("+CGPADDR:") == -1) return false;
  if (resp.indexOf("0.0.0.0") != -1) return false;
  if (resp.indexOf('.') == -1) return false;
  return true;
}

// Configure APN, (re)attach and activate PDP, check IP; try CHAP if PAP fails
static bool setupAPNContext(const char* apn) {
  Serial.print("➡️ Setze APN: ");
  Serial.println(apn);
  // Detach then configure
  sendATCommand("AT+CGATT=0", 5000);
  delay(300);
  sendATCommand("AT+CGDCONT=1,\"IP\",\"" + String(apn) + "\"", 3000);
  if (String(APN_USER).length() > 0 || String(APN_PASS).length() > 0) {
    // PAP first
    sendATCommand("AT+CGAUTH=1,1,\"" + String(APN_USER) + "\",\"" + String(APN_PASS) + "\"", 5000);
  }
  // Attach and activate
  sendATCommand("AT+CGATT=1", 12000);
  // Registration wait (best effort)
  (void)isRegistered(15000);
  sendATCommand("AT+CGACT=1,1", 15000);
  if (hasIP()) return true;

  // Fallback to CHAP if credentials provided
  if (String(APN_USER).length() > 0 || String(APN_PASS).length() > 0) {
    Serial.println("Fallback to CHAP auth...");
    sendATCommand("AT+CGACT=0,1", 8000);
    sendATCommand("AT+CGAUTH=1,2,\"" + String(APN_USER) + "\",\"" + String(APN_PASS) + "\"", 5000);
    sendATCommand("AT+CGACT=1,1", 15000);
    if (hasIP()) return true;
  }
  return false;
}

// Ensure SIM is ready; if SIM_PIN is provided and required, enter it and wait for READY
bool ensureSimReady(unsigned long timeoutMs) {
  unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    String resp;
    if (!sendAT("AT+CPIN?", resp, 3000)) {
      delay(1000);
      continue;
    }
    if (resp.indexOf("READY") != -1) {
      Serial.println("SIM is READY");
      return true;
    }
    if (resp.indexOf("SIM PIN") != -1) {
      if (String(SIM_PIN).length() > 0) {
        Serial.println("Entering SIM PIN...");
        if (!sendATCommand("AT+CPIN=\"" + String(SIM_PIN) + "\"", 5000)) {
          Serial.println("Failed to send CPIN");
        }
        // Give the SIM time to unlock
        delay(5000);
      } else {
        Serial.println("SIM requires PIN but SIM_PIN is empty");
        return false;
      }
    } else if (resp.indexOf("PUK") != -1) {
      Serial.println("SIM PUK required – cannot proceed");
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
  // Ensure SIM is unlocked and ready
  if (!ensureSimReady()) {
    Serial.println("SIM not ready – aborting network attach");
    return;
  }

  // Verbose errors for debugging
  sendATCommand("AT+CMEE=2", 500);

  // First try with configured APN
  bool ok = setupAPNContext(APN);

  // APN fallback if initial APN failed
  if (!ok) {
    if (String(APN) == String("data.swisscom.ch")) {
      Serial.println("⚠️ APN fallback auf gprs.swisscom.ch...");
      ok = setupAPNContext("gprs.swisscom.ch");
    }
  }

  // Final registration check
  bool reg = isRegistered(10000);
  is_connected = ok && reg;

  if (is_connected) {
    Serial.println("Connected to cellular network (PDP active, IP assigned)");
    digitalWrite(STATUS_LED, HIGH);
  } else {
    Serial.println("Failed to establish data connection – check SIM, APN, or signal");
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
  
  // Magnetometer support removed; using Hall GPIO exclusively
  
  // Check initial barrier position
  // With servo, track position via state; with relays, use limit switch
#if USE_SERVO
  state.barrier_up = false; // assume start in DOWN position
#else
  state.barrier_up = digitalRead(LIMIT_UP) == LOW;
#endif
  
  Serial.println("Sensors initialized");
}

void updateSensorReadings() {
  // Read ultrasonic distance
  float distance = readUltrasonicDistance();
  
  // Determine occupancy (car typically 15-50cm from sensor)
  bool was_occupied = state.is_occupied;
  bool occupancy_ultra = (distance > 15 && distance < 200);

  // Read hall sensor (active LOW when magnet present)
  bool hall_present = (digitalRead(HALL_SENSOR) == LOW);
  state.hall_detected = hall_present;

  // Combine: consider spot occupied if either ultrasonic indicates presence
  // or magnet is detected by the hall sensor
  state.is_occupied = occupancy_ultra || hall_present;
  
  // Motion detection
  if (digitalRead(MOTION_SENSOR) == HIGH) {
    state.last_motion = millis();
  }
  
  // Power readings
  state.battery_level = readBatteryLevel();
  state.solar_voltage = readSolarVoltage();
  
  // Barrier position
#if !USE_SERVO
  state.barrier_up = digitalRead(LIMIT_UP) == LOW;
#endif
  
  // Temperature (stubbed)
  state.temperature = getTemperature();
  
  // Log occupancy changes
  if (state.is_occupied != was_occupied) {
    Serial.println("Occupancy changed: " + String(state.is_occupied ? "OCCUPIED" : "FREE"));
    Serial.println("Distance: " + String(distance) + "cm");
    Serial.print("Hall detected: "); Serial.println(state.hall_detected ? "YES" : "NO");
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
  
  bool ok = false;
  for (int attempt = 1; attempt <= 3 && !ok; ++attempt) {
    ok = sendHTTPRequest("POST", "/hardware/register", payload);
    if (!ok) {
      Serial.print("Register attempt "); Serial.print(attempt); Serial.println(" failed");
      if (attempt < 3) delay(1000UL * attempt); // 1s, 2s backoff
    }
  }
  if (ok) {
    Serial.println("Device registered successfully");
    device_registered = true;
  } else {
    Serial.println("Failed to register device");
    device_registered = false;
  }
  last_register_try = millis();
}

void sendHeartbeat() {
  if (g_disableModem) {
    return;
  }
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
  // Read actual RSSI via AT+CSQ and convert to dBm
  state.signal_strength = readSignalStrengthDbm();
  doc["signal_strength"] = state.signal_strength;
  doc["temperature"] = state.temperature;
  doc["hall_detected"] = state.hall_detected;

  
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
  if (g_disableModem) return;
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
  } else if (command == "set_verbose") {
    // parameters: {"enabled": true/false, "persist": optional bool}
    bool enabled = parameters.containsKey("enabled") ? (bool)parameters["enabled"] : g_verbose;
    g_verbose = enabled;
    bool persist = parameters.containsKey("persist") ? (bool)parameters["persist"] : true;
    if (persist) saveSettingsToEEPROM();
    Serial.print("Verbose logging set to "); Serial.println(g_verbose ? "ON" : "OFF");
  } else if (command == "set_servo_positions") {
    // parameters: {"up_us": 2000, "down_us": 1000, "delay_ms": 900, "persist": true}
    if (parameters.containsKey("up_us"))   servoPosUpUs = constrain((int)parameters["up_us"], 500, 2500);
    if (parameters.containsKey("down_us")) servoPosDownUs = constrain((int)parameters["down_us"], 500, 2500);
    if (parameters.containsKey("delay_ms")) servoMoveDelayMs = constrain((int)parameters["delay_ms"], 100, 5000);
    bool persist = parameters.containsKey("persist") ? (bool)parameters["persist"] : true;
    if (persist) saveSettingsToEEPROM();
    Serial.print("Servo positions updated: up="); Serial.print(servoPosUpUs);
    Serial.print(" us, down="); Serial.print(servoPosDownUs);
    Serial.print(" us, delay="); Serial.print(servoMoveDelayMs); Serial.println(" ms");
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

#if USE_SERVO
  // Drive servo to UP position
  moveServoToUs(servoPosUpUs);
  delay(servoMoveDelayMs);
  state.barrier_up = true;
  Serial.println("Barrier raised (servo)");
#else
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
#endif
}

void lowerBarrier() {
  if (state.emergency_stop) return;
  
  Serial.println("Lowering barrier...");

#if USE_SERVO
  // Drive servo to DOWN position
  moveServoToUs(servoPosDownUs);
  delay(servoMoveDelayMs);
  state.barrier_up = false;
  Serial.println("Barrier lowered (servo)");
#else
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
#endif
}

// ========== HTTP COMMUNICATION ==========
bool sendHTTPRequest(String method, String endpoint, String payload, String* response) {
  String url = String(API_BASE) + endpoint;
  bool use_https = url.startsWith("https://");
  // Extract hostname for DNS resolution diagnostics
  String host = url;
  if (host.startsWith("http://")) host.remove(0, 7);
  if (host.startsWith("https://")) host.remove(0, 8);
  int slashPos = host.indexOf('/');
  if (slashPos > 0) host = host.substring(0, slashPos);

  auto readUntil = [&](const String& token, unsigned long timeoutMs) -> String {
    String buf;
    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
      while (sim800.available()) {
        char c = (char)sim800.read();
        buf += c;
        if (buf.length() > 1024) buf.remove(0, buf.length() - 1024);
        if (buf.indexOf(token) != -1) {
          return buf;
        }
      }
      delay(1);
    }
    return buf; // may be empty or partial
  };

  auto readFor = [&](unsigned long ms) -> String {
    String buf;
    unsigned long start = millis();
    while (millis() - start < ms) {
      while (sim800.available()) {
        buf += (char)sim800.read();
      }
      delay(1);
    }
    return buf;
  };

  // Read exactly N bytes from modem (or until timeout)
  auto readExact = [&](size_t n, unsigned long timeoutMs) -> String {
    String buf;
    unsigned long start = millis();
    while (buf.length() < (int)n && (millis() - start) < timeoutMs) {
      while (sim800.available() && buf.length() < (int)n) {
        buf += (char)sim800.read();
      }
      delay(1);
    }
    return buf;
  };

  // TLS config for SIM7600 (HTTPSSL context uses default SSL config index)
  if (use_https) {
    sim800.println("AT+CSSLCFG=\"sslversion\",1,4"); // 4 = TLS1.2
  (void)readFor(g_verbose ? 120 : 40);
    sim800.println("AT+CSSLCFG=\"sni\",1");          // enable SNI
  (void)readFor(g_verbose ? 120 : 40);
    sim800.println("AT+CSSLCFG=\"seclevel\",0");      // 0 = no server cert verification (dev)
  (void)readFor(g_verbose ? 120 : 40);
    // Broaden cipher suite selection (0 = auto/all supported)
    sim800.println("AT+CSSLCFG=\"cipher\",1,0");
    (void)readFor(g_verbose ? 120 : 40);
    // Increase SSL negotiation timeout for slow networks (seconds)
    sim800.println("AT+CSSLCFG=\"negotiatetime\",1,120");
    (void)readFor(g_verbose ? 150 : 60);
  // Note: keep TLS settings minimal; additional CSSLCFG options vary by firmware
  }

  // Init HTTP
  // Best-effort cleanup in case previous session wasn't closed
  sim800.println("AT+HTTPTERM");
  (void)readFor(200);
  sim800.println("AT+HTTPINIT");
  (void)readUntil("OK", 1500);
  // Make sure PDP context 1 is used explicitly for HTTP
  sim800.println("AT+HTTPPARA=\"CID\",1");
  (void)readUntil("OK", 800);
  sim800.println("AT+HTTPPARA=\"CID\",1");
  (void)readUntil("OK", 800);
  sim800.println("AT+HTTPPARA=\"REDIR\",1"); // follow redirects
  (void)readUntil("OK", 800);
  // Extend overall HTTP action timeout to 60s
  sim800.println("AT+HTTPPARA=\"TIMEOUT\",60");
  (void)readUntil("OK", 800);

  // Enable/disable SSL depending on URL scheme
  sim800.println(String("AT+HTTPSSL=") + (use_https ? "1" : "0"));
  (void)readUntil("OK", 800);

  // URL
  sim800.println("AT+HTTPPARA=\"URL\",\"" + url + "\"");
  (void)readUntil("OK", 1200);

  // Optional: set a User-Agent (some edges behave better)
  sim800.println("AT+HTTPPARA=\"UA\",\"ESP32-SIM7600/1.0\"");
  (void)readFor(150);

  // Optional: resolve DNS first to ensure name can be resolved
  // Set fallback DNS resolvers to improve reliability on some networks
  sim800.println("AT+CDNSCFG=\"8.8.8.8\",\"1.1.1.1\"");
  (void)readUntil("OK", 1500);
  sim800.println("AT+CDNSGIP=\"" + host + "\"");
  String dns = readUntil("OK", 8000);
  if (dns.indexOf("+CDNSGIP:") != -1) {
    Serial.print("DNS resolved: "); Serial.println(dns);
  } else {
    Serial.print("DNS resolution pending/failed for host "); Serial.println(host);
  }

  // POST body if applicable
  if (method == "POST") {
    sim800.println("AT+HTTPPARA=\"CONTENT\",\"application/json\"");
    (void)readUntil("OK", 800);
    sim800.println("AT+HTTPDATA=" + String(payload.length()) + ",10000");
    // Wait for DOWNLOAD prompt
    (void)readUntil("DOWNLOAD", 3000);
    sim800.print(payload);
    // Wait for OK after sending data
    (void)readUntil("OK", 5000);
  }

  // Perform action: 0=GET, 1=POST
  simDrain(50);
  sim800.println(String("AT+HTTPACTION=") + (method == "POST" ? "1" : "0"));
  // Robust wait for URC: keep collecting until we see +HTTPACTION: or timeout
  String actionResp;
  {
    unsigned long start = millis();
    int tokenIndex = -1;
    while (millis() - start < 90000UL) { // up to 90s for TLS over LTE
      while (sim800.available()) {
        char c = (char)sim800.read();
        actionResp += c;
  if (actionResp.length() > 4096) actionResp.remove(0, actionResp.length() - 2048);
      }
      tokenIndex = actionResp.indexOf("+HTTPACTION:");
      if (tokenIndex != -1) {
        // After we first see the token, wait for end-of-line to get full numbers
        unsigned long moreUntil = millis() + 3000;
        while (millis() < moreUntil) {
          while (sim800.available()) {
            char c = (char)sim800.read();
            actionResp += c;
            if (actionResp.length() > 4096) actionResp.remove(0, actionResp.length() - 2048);
          }
          // Line ends with \n after the URC
          if (actionResp.indexOf('\n', tokenIndex) != -1) break;
          delay(10);
        }
        break;
      }
      delay(20);
    }
  }

  // Parse status and data length
  int status = -1;
  int dataLen = 0;
  {
    // Expect "+HTTPACTION: <m>,<status>,<len>"
    int idx = actionResp.indexOf("+HTTPACTION:");
    if (idx != -1) {
      // find the comma-separated numbers
      // skip to first comma
      int c1 = actionResp.indexOf(',', idx);
      int c2 = actionResp.indexOf(',', c1 + 1);
      if (c1 != -1 && c2 != -1) {
        status = actionResp.substring(c1 + 1, c2).toInt();
        // read until end of line for len
        int endLine = actionResp.indexOf('\n', c2 + 1);
        String lenStr = actionResp.substring(c2 + 1, endLine == -1 ? actionResp.length() : endLine);
        dataLen = lenStr.toInt();
      }
    }
  }

  // Read body if any
  String body = "";
  if (dataLen > 0) {
    // Ask modem to return exactly dataLen bytes from start of body
    sim800.println("AT+HTTPREAD=0," + String(dataLen));
    // Wait for header line "+HTTPREAD: <len>\r\n"
    (void)readUntil("+HTTPREAD:", 3000);
    (void)readUntil("\n", 1000); // consume header line fully
    // Now read exact body bytes
    body = readExact((size_t)dataLen, min(25000UL, 4000UL + (unsigned long)dataLen));
    // Consume trailing CRLF and OK if present (do not append to body)
    (void)readUntil("OK", 2000);
  }

  if (response) {
    *response = body;
  }

  // Terminate HTTP
  sim800.println("AT+HTTPTERM");
  String termResp = readUntil("OK", g_verbose ? 1500 : 600);
  if (termResp.indexOf("OK") == -1) {
    // Some firmwares may return ERROR if already terminated
  (void)readUntil("ERROR", g_verbose ? 800 : 300);
  }
  // Drain any leftover bytes to avoid stray prints later
  simDrain(g_verbose ? 80 : 20);

  // Log status and snippet
  Serial.print("HTTP "); Serial.print(method); Serial.print(" "); Serial.print(url);
  Serial.print(" -> status="); Serial.print(status);
  Serial.print(" len="); Serial.print(dataLen);
  if (g_verbose) {
    if (actionResp.length() > 0) { Serial.print(" actionResp="); Serial.print(actionResp); }
    if (body.length() > 0) {
      String snippet = body.substring(0, min(120, (int)body.length()));
      Serial.print(" body[0:120]="); Serial.println(snippet);
    } else {
      Serial.println();
    }
  } else {
    Serial.println();
  }

  return status >= 200 && status < 300;
}

// Convert AT+CSQ to dBm. Returns -999 on failure.
int readSignalStrengthDbm() {
  String resp;
  if (!sendAT("AT+CSQ", resp, 1500)) return -999;
  // +CSQ: <rssi>,<ber>
  int p = resp.indexOf("+CSQ:");
  if (p == -1) return -999;
  int comma = resp.indexOf(',', p);
  if (comma == -1) return -999;
  // Extract number after "+CSQ: " up to comma
  int start = resp.indexOf(':', p);
  if (start == -1) return -999;
  start += 1;
  while (start < (int)resp.length() && (resp[start] == ' ' || resp[start] == '\r' || resp[start] == '\n')) start++;
  int endNum = comma;
  while (endNum > start && (resp[endNum-1] == ' ')) endNum--;
  int rssiVal = resp.substring(start, endNum).toInt();
  if (rssiVal == 99) return -999; // unknown/undetectable
  // CSQ rssi 0..31 -> dBm = -113 + 2*rssi
  int dbm = -113 + 2 * rssiVal;
  return dbm;
}

// ========== POWER MANAGEMENT ==========
void managePower() {
  // Enter deep sleep if battery low and no activity
  if (is_connected && state.battery_level < 20 && millis() - state.last_motion > 300000) {
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

// (Magnetometer helpers removed per user request)
# Prüfen, ob der Benutzer noch existiert
id assistant-temp || echo "assistant-temp nicht vorhanden"

# Sicherstellen, dass Home weg ist (falls entfernt)
ls -ld /home/assistant-temp || echo "/home/assistant-temp nicht vorhanden"

# Optional: bestätige, dass kein authorized_keys mehr existiert
test -f /home/assistant-temp/.ssh/authorized_keys && echo "authorized_keys noch vorhanden" || echo "authorized_keys entfernt"