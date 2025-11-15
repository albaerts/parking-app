// MMC5603 Example for ESP32 (Arduino)
// Uses Adafruit MMC5603 library with a fallback direct-register read path
// that you provided (works when the library begin() sometimes fails).
// Replace WIFI_SSID / WIFI_PASS with your credentials before flashing.

#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_MMC56x3.h>

// --- User configuration ---
const char* WIFI_SSID = "YOUR_SSID"; // replace
const char* WIFI_PASS = "YOUR_PASSWORD"; // replace
const char* BACKEND_URL = "https://parking.gashis.ch/api/device/event";
const char* DEVICE_ID = "PARK_DEVICE_001";

// Sampling / detection params
const int SAMPLE_HZ = 25;
const int WINDOW_SIZE = 10;
const unsigned long DEBOUNCE_MS = 2500;

// I2C pins (user provided)
// SDA -> GPIO21, SCL -> GPIO22 (updated per user)
const int I2C_SDA = 21;
const int I2C_SCL = 22;

// MMC5603 address / regs
const uint8_t MMC5603_ADDR = 0x30;
#define REG_OUT_X_L   0x00
#define REG_STATUS    0x18
#define REG_ODR       0x1A
#define REG_CTRL0     0x1B
#define REG_CTRL1     0x1C
#define REG_CTRL2     0x1D
#define REG_PRODUCT_ID 0x39

Adafruit_MMC5603 mag;
// runtime state
bool fallbackMode = false;
float window[WINDOW_SIZE];
int wpos = 0;
float windowSum = 0;

float baseline = 0;
float sigma_val = 0;
bool calibrated = false;
unsigned long lastChangeTs = 0;
bool occupied = false;
unsigned long lastSample = 0;
unsigned long lastRawPrint = 0;

// --- Helpers: I2C read/write / fallback raw reads ---
bool i2cPing(uint8_t addr) {
  Wire.beginTransmission(addr);
  return (Wire.endTransmission() == 0);
}
uint8_t rd8(uint8_t reg) {
  Wire.beginTransmission(MMC5603_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0xFF;
  Wire.requestFrom(MMC5603_ADDR, (uint8_t)1);
  if (!Wire.available()) return 0xFF;
  return Wire.read();
}
bool wr8(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MMC5603_ADDR);
  Wire.write(reg);
  Wire.write(val);
  return (Wire.endTransmission() == 0);
}
bool tmTriggerMag() {
  if (!wr8(REG_CTRL0, 0x01)) return false; // TM_M
  uint32_t t0 = millis();
  while (!(rd8(REG_STATUS) & (1 << 6))) {   // MAG_RDY
    if (millis() - t0 > 100) return false;
    delay(5);
  }
  return true;
}
bool readMagXYZ(float &mx, float &my, float &mz) {
  Wire.beginTransmission(MMC5603_ADDR);
  Wire.write(REG_OUT_X_L);
  if (Wire.endTransmission(false) != 0) return false;
  Wire.requestFrom(MMC5603_ADDR, (uint8_t)9);
  if (Wire.available() < 9) return false;
  uint8_t b[9];
  for (int i = 0; i < 9; i++) b[i] = Wire.read();

  int32_t x = ((uint32_t)b[0] << 12) | ((uint32_t)b[1] << 4) | (b[6] >> 4);
  int32_t y = ((uint32_t)b[2] << 12) | ((uint32_t)b[3] << 4) | (b[7] >> 4);
  int32_t z = ((uint32_t)b[4] << 12) | ((uint32_t)b[5] << 4) | (b[8] >> 4);
  x -= (uint32_t)1 << 19;
  y -= (uint32_t)1 << 19;
  z -= (uint32_t)1 << 19;

  mx = (float)x * 0.00625f;
  my = (float)y * 0.00625f;
  mz = (float)z * 0.00625f;
  return true;
}

// Unified read that prefers library path, falls back to register reads
bool readMagToFloats(float &mx, float &my, float &mz) {
  if (!fallbackMode) {
    sensors_event_t e;
    mag.getEvent(&e);
    mx = e.magnetic.x;
    my = e.magnetic.y;
    mz = e.magnetic.z;
    return true;
  } else {
    return readMagXYZ(mx, my, mz);
  }
}

void sendEvent(bool occ) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  String body = String("{\"device_id\":\"") + DEVICE_ID + String("\",\"occupied\":") + (occ ? "true" : "false") + String("}");
  int code = http.POST(body);
  Serial.printf("POST %s -> %d\n", body.c_str(), code);
  http.end();
}

void calibrateBaseline(int seconds=15) {
  Serial.println("Calibrating baseline...");
  int samples = seconds * SAMPLE_HZ;
  double sum = 0;
  double sum2 = 0;
  for (int i=0;i<samples;i++) {
    while (millis() - lastSample < 1000 / SAMPLE_HZ) delay(1);
    lastSample = millis();
    float mx, my, mz;
    if (!readMagToFloats(mx, my, mz)) {
      // if a read fails, back off and retry
      i--; delay(5); continue;
    }
    float M = sqrt(mx*mx + my*my + mz*mz);
    sum += M;
    sum2 += M*M;
  }
  baseline = sum / samples;
  float var = (sum2 / samples) - (baseline*baseline);
  sigma_val = var > 0 ? sqrt(var) : 0;
  Serial.printf("Baseline=%.2f uT sigma=%.2f\n", baseline, sigma_val);
  calibrated = true;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("MMC5603 field-ready example starting...");

  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(100000); // 100 kHz = robust
  Serial.printf("I2C SDA=%d SCL=%d\n", I2C_SDA, I2C_SCL);

  // Try library init first (user-tested signature)
  if (mag.begin(MMC5603_ADDR, &Wire)) {
    Serial.println("MMC5603 found (library mode)");
    fallbackMode = false;
  } else {
    Serial.println("Library begin() failed — trying fallback checks...");
    // manual I2C ping
    if (!i2cPing(MMC5603_ADDR)) {
      Serial.println("Error: no I2C device at 0x30 found!");
      while (1) { delay(1000); }
    }
    uint8_t pid = rd8(REG_PRODUCT_ID);
    if (pid == 0x10 || pid == 0x00) {
      // Minimal init sequence (from your working fallback)
      wr8(REG_CTRL1, 0x80); delay(50);   // Soft Reset
      wr8(REG_CTRL2, 0x00); delay(5);    // Continuous Mode off
      wr8(REG_CTRL0, 0x08); delay(2);    // Set
      wr8(REG_CTRL0, 0x10); delay(2);    // Reset
      wr8(REG_ODR, 0x32);   delay(5);    // moderate ODR
      Serial.println("MMC5603 found (fallback mode)");
      fallbackMode = true;
    } else {
      Serial.println("Error: unexpected PRODUCT_ID — sensor might be defective.");
      while (1) { delay(1000); }
    }
  }

  // connect WiFi (non-blocking-ish)
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 15000) {
    Serial.print('.');
    delay(500);
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) Serial.println("WiFi connected");
  else Serial.println("WiFi not connected (ok for offline testing)");

  for (int i=0;i<WINDOW_SIZE;i++) window[i]=0;
  lastSample = millis();
  calibrateBaseline(10); // shorter default calibration
  for (int i=0;i<WINDOW_SIZE;i++) { window[i] = baseline; windowSum += window[i]; }
}

void loop() {
  if (millis() - lastSample < 1000 / SAMPLE_HZ) { delay(1); return; }
  lastSample = millis();

  float mx, my, mz;
  if (!readMagToFloats(mx, my, mz)) {
    Serial.println("Mag read failed — will retry");
    return;
  }
  float M = sqrt(mx*mx + my*my + mz*mz);

  // Raw output for field debugging — at least 1x per second
  if (millis() - lastRawPrint >= 1000) {
    Serial.printf("RAW: mx=%.2f uT my=%.2f uT mz=%.2f uT | M=%.2f uT\n", mx, my, mz, M);
    lastRawPrint = millis();
  }

  // moving average
  windowSum -= window[wpos];
  windowSum += M;
  window[wpos] = M;
  wpos = (wpos + 1) % WINDOW_SIZE;
  float Mavg = windowSum / WINDOW_SIZE;

  float T_on = max(10.0f, max(baseline*0.05f, 3.0f * sigma_val));
  float T_off = T_on * 0.6f;
  bool newOcc = occupied;
  if (!occupied && fabs(Mavg - baseline) > T_on) {
    if (millis() - lastChangeTs > DEBOUNCE_MS) {
      newOcc = true;
      lastChangeTs = millis();
    }
  } else if (occupied && fabs(Mavg - baseline) < T_off) {
    if (millis() - lastChangeTs > DEBOUNCE_MS) {
      newOcc = false;
      lastChangeTs = millis();
    }
  } else {
    lastChangeTs = millis();
  }

  if (newOcc != occupied) {
    occupied = newOcc;
    Serial.printf("State changed: occupied=%d Mavg=%.2f baseline=%.2f T_on=%.2f\n", occupied, Mavg, baseline, T_on);
    sendEvent(occupied);
  }
}
// MMC5603 Example for ESP32 (Arduino)
// Uses Adafruit MMC5603 library
// SDA -> GPIO32, SCL -> GPIO33 on this board (user-provided pins)
// Replace WIFI_SSID / WIFI_PASS with your credentials before flashing

#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_MMC56x3.h>

// --- User configuration ---
const char* WIFI_SSID = "YOUR_SSID"; // replace
const char* WIFI_PASS = "YOUR_PASSWORD"; // replace
const char* BACKEND_URL = "https://parking.gashis.ch/api/device/event";
const char* DEVICE_ID = "PARK_DEVICE_001";

// Sampling / detection params
const int SAMPLE_HZ = 25;
const int WINDOW_SIZE = 10;
const unsigned long DEBOUNCE_MS = 2500;

// I2C pins (user provided)
// SDA -> GPIO21, SCL -> GPIO22 (updated per user)
const int I2C_SDA = 21;
const int I2C_SCL = 22;

Adafruit_MMC5603 mag;
float window[WINDOW_SIZE];
int wpos = 0;
float windowSum = 0;

float baseline = 0;
float sigma_val = 0;
bool calibrated = false;
unsigned long lastChangeTs = 0;
bool occupied = false;
unsigned long lastSample = 0;

void sendEvent(bool occ) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  String body = String("{\"device_id\":\"") + DEVICE_ID + String("\",\"occupied\":") + (occ ? "true" : "false") + String("}");
  int code = http.POST(body);
  Serial.printf("POST %s -> %d\n", body.c_str(), code);
  http.end();
}

void calibrateBaseline(int seconds=15) {
  Serial.println("Calibrating baseline...");
  int samples = seconds * SAMPLE_HZ;
  double sum = 0;
  double sum2 = 0;
  for (int i=0;i<samples;i++) {
    while (millis() - lastSample < 1000 / SAMPLE_HZ) delay(1);
    lastSample = millis();
    sensors_event_t event;
    mag.getEvent(&event);
    float mx = event.magnetic.x;
    float my = event.magnetic.y;
    float mz = event.magnetic.z;
    float M = sqrt(mx*mx + my*my + mz*mz);
    sum += M;
    sum2 += M*M;
  }
  baseline = sum / samples;
  float var = (sum2 / samples) - (baseline*baseline);
  sigma_val = var > 0 ? sqrt(var) : 0;
  Serial.printf("Baseline=%.2f uT sigma=%.2f\n", baseline, sigma_val);
  calibrated = true;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Wire.begin(I2C_SDA, I2C_SCL);
  Serial.printf("I2C SDA=%d SCL=%d\n", I2C_SDA, I2C_SCL);

  if (!mag.begin()) {
    Serial.println("MMC5603 not found on I2C bus!");
    while (1) delay(1000);
  }

  // connect WiFi (non-blocking-ish)
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 15000) {
    Serial.print('.');
    delay(500);
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) Serial.println("WiFi connected");
  else Serial.println("WiFi not connected (ok for offline testing)");

  for (int i=0;i<WINDOW_SIZE;i++) window[i]=0;
  lastSample = millis();
  calibrateBaseline(10); // shorter default calibration
  for (int i=0;i<WINDOW_SIZE;i++) { window[i] = baseline; windowSum += window[i]; }
}

void loop() {
  if (millis() - lastSample < 1000 / SAMPLE_HZ) { delay(1); return; }
  lastSample = millis();

  sensors_event_t event;
  mag.getEvent(&event);
  float mx = event.magnetic.x;
  float my = event.magnetic.y;
  float mz = event.magnetic.z;
  float M = sqrt(mx*mx + my*my + mz*mz);

  // moving average
  windowSum -= window[wpos];
  windowSum += M;
  window[wpos] = M;
  wpos = (wpos + 1) % WINDOW_SIZE;
  float Mavg = windowSum / WINDOW_SIZE;

  float T_on = max(10.0f, max(baseline*0.05f, 3.0f * sigma_val));
  float T_off = T_on * 0.6f;
  bool newOcc = occupied;
  if (!occupied && fabs(Mavg - baseline) > T_on) {
    if (millis() - lastChangeTs > DEBOUNCE_MS) {
      newOcc = true;
      lastChangeTs = millis();
    }
  } else if (occupied && fabs(Mavg - baseline) < T_off) {
    if (millis() - lastChangeTs > DEBOUNCE_MS) {
      newOcc = false;
      lastChangeTs = millis();
    }
  } else {
    lastChangeTs = millis();
  }

  if (newOcc != occupied) {
    occupied = newOcc;
    Serial.printf("State changed: occupied=%d Mavg=%.2f baseline=%.2f T_on=%.2f\n", occupied, Mavg, baseline, T_on);
    sendEvent(occupied);
  }
}
