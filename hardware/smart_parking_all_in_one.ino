/*
  Smart Parking - All-in-One (ESP32)

  Features
  - SG92R Servo barrier control (GPIO 18)
  - Hall sensor (A3144) for vehicle detection (GPIO 19, internal pull-up)
  - Status LED (GPIO 2) optional
  - Optional WiFi + HTTP PUT to backend /parking-spots/{id}/status

  IMPORTANT
  - Power the servo from a stable 5V source (e.g., Pololu S13V20F5). Do NOT power the servo from the ESP32 5V pin if unsure.
  - Connect grounds together: Servo GND, ESP32 GND, Sensor GND, Power GND.
  - Adjust CLOSED_ANGLE and OPEN_ANGLE to your mechanics.

  Libraries
  - ESP32 board support (Arduino IDE > Boards Manager > ESP32 by Espressif)
  - ESP32Servo by Kevin Harrington (Library Manager) for Servo on ESP32
*/
/*
  Smart Parking – All-in-One (ESP32)

  Funktionen
  - SG92R/SG90 Servo zur Barrierensteuerung (GPIO 18)
  - Hall-Sensor (A3144) zur Fahrzeugerkennung (GPIO 19, interner Pull-up)
  - Status-LED (GPIO 2) optional
  - Optional: WiFi + HTTP PUT an Backend /parking-spots/{id}/status

  WICHTIG
  - Servo aus stabiler 5V-Quelle versorgen (z. B. Pololu S13V20F5). Nicht unsicher über den ESP32-5V-Pin speisen.
  - Alle Massen (GND) verbinden: Servo GND, ESP32 GND, Sensor GND, Versorgung GND.
  - CLOSED_ANGLE und OPEN_ANGLE an die Mechanik anpassen.

  Bibliotheken
  - ESP32 Board Support (Arduino IDE > Boardverwalter > ESP32 by Espressif)
  - ESP32Servo von Kevin Harrington (Bibliotheksverwalter) für Servo auf ESP32
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// ----- Pins -----
const int SERVO_PIN = 18;      // PWM capable
const int HALL_PIN = 19;       // A3144, internen Pull-up verwenden
const int LED_PIN = 2;         // Onboard LED on many dev boards (set to -1 to disable)

// ----- Servo angles (adjust!) -----
const int CLOSED_ANGLE = 110;  // barrier down
const int OPEN_ANGLE = 20;     // barrier up

// ----- Hall logic -----
// A3144 zieht üblicherweise auf LOW, wenn ein Magnetfeld anliegt. Ggf. invertieren.
// We interpret: LOW = occupied (car present), HIGH = free
const bool HALL_LOW_IS_OCCUPIED = true;

// Debounce/hysteresis timings (ms)
const uint32_t OCCUPIED_CONFIRM_MS = 200;  // require LOW stable this long to mark occupied
const uint32_t FREE_CONFIRM_MS = 400;      // require HIGH stable this long to mark free

// ----- WiFi/Backend (optional) -----
// Set your WiFi credentials and backend. Leave SSID empty to run offline.
const char* WIFI_SSID = "";           // e.g. "MyWiFi"
const char* WIFI_PASS = "";           // z. B. "passwort123"

// IMPORTANT: Use your Mac/Server LAN IP, not 127.0.0.1
// Example: "http://192.168.1.23:8000"
String BACKEND_BASE = "http://192.168.0.100:8000";  // CHANGE ME
int PARKING_SPOT_ID = 1;                              // CHANGE if needed

// ----- Runtime state -----
Servo barrier;
bool isOccupied = false;           // last known logical status
uint32_t stateChangeAt = 0;        // last transition time for debounce
int lastRaw = HIGH;                // previous raw read

// ----- Helpers -----
void setBarrier(bool occupied) {
  // Move servo to desired angle
  int target = occupied ? CLOSED_ANGLE : OPEN_ANGLE; 
  barrier.write(target);
  if (LED_PIN >= 0) {
    digitalWrite(LED_PIN, occupied ? HIGH : LOW);
  }
}

void announceStatusSerial() {
  Serial.print("Status: ");
  Serial.println(isOccupied ? "occupied" : "free");
}

bool wifiConfigured() {
  return WIFI_SSID && strlen(WIFI_SSID) > 0;
}

void wifiConnectIfNeeded() {
  if (!wifiConfigured()) return;
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Verbinde WiFi mit "); Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 8000) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK, IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi nicht verbunden (Offline-Modus)");
  }
}

void sendStatusToBackend() {
  if (!wifiConfigured()) return;
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnectIfNeeded();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  String url = BACKEND_BASE + "/parking-spots/" + String(PARKING_SPOT_ID) + "/status";
  String payload = String("{\"status\":\"") + (isOccupied ? "occupied" : "free") + "\"}";

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  int code = http.PUT(payload);
  if (code > 0) {
    Serial.print("Backend PUT "); Serial.print(url);
    Serial.print(" => "); Serial.println(code);
  } else {
    Serial.print("HTTP-Fehler: "); Serial.println(code);
  }
  http.end();
}

void updateStatusIfStable(int raw) {
  // raw: LOW or HIGH
  uint32_t now = millis();

  // On transition, reset timer
  if (raw != lastRaw) {
    lastRaw = raw;
    stateChangeAt = now;
    return;
  }

  // Stable long enough?
  if (raw == LOW) {
    if (!isOccupied && (now - stateChangeAt >= OCCUPIED_CONFIRM_MS)) {
      isOccupied = true;
      setBarrier(isOccupied);
      announceStatusSerial();
      sendStatusToBackend();
    }
  } else { // raw == HIGH
    if (isOccupied && (now - stateChangeAt >= FREE_CONFIRM_MS)) {
      isOccupied = false;
      setBarrier(isOccupied);
      announceStatusSerial();
      sendStatusToBackend();
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\nSmart Parking (All-in-One) starting...");

  if (LED_PIN >= 0) {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
  }

  // Hall-Sensor mit internem Pull-up
  pinMode(HALL_PIN, INPUT_PULLUP);
  lastRaw = digitalRead(HALL_PIN);
  stateChangeAt = millis();

  // Servo setup
  // Set a low frequency safe for SG90/92R (typical 50 Hz)
  // ESP32Servo automatically uses a PWM channel
  barrier.setPeriodHertz(50); 
  barrier.attach(SERVO_PIN, 500, 2500); // min/max uS (tune if needed)

  // Initialize barrier to CLOSED then move to initial state
  barrier.write(CLOSED_ANGLE); 
  delay(400);

  // Determine initial logical state from raw
  bool initialOccupied = HALL_LOW_IS_OCCUPIED ? (lastRaw == LOW) : (lastRaw == HIGH);
  isOccupied = initialOccupied;
  setBarrier(isOccupied);
  announceStatusSerial();

  // WiFi optional
  wifiConnectIfNeeded();
  sendStatusToBackend(); // announce initial state (if WiFi)
}

void loop() {
  int raw = digitalRead(HALL_PIN);
  int logical = raw; // keep name for clarity
  if (!HALL_LOW_IS_OCCUPIED) logical = (raw == LOW) ? HIGH : LOW; // invert if needed

  updateStatusIfStable(logical);
  delay(10); // loop tick
}
