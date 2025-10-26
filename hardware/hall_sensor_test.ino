// Updated to match main firmware: Hall sensor on GPIO32 (INPUT_PULLUP)
#define HALL_PIN 32

// Optional: einfache Entprellung
unsigned long lastChange = 0;
bool lastState = HIGH; // INPUT_PULLUP: HIGH = frei

void setup() {
  Serial.begin(115200);
  pinMode(HALL_PIN, INPUT_PULLUP);
  Serial.println("Hall-Sensor-Test gestartet");
}

void loop() {
  bool cur = digitalRead(HALL_PIN);
  if (cur != lastState && (millis() - lastChange) > 50) { // 50ms debounce
    lastChange = millis();
    lastState = cur;
    if (cur == LOW) {
      Serial.println("🚗 Fahrzeug ERKANNT (LOW)");
    } else {
      Serial.println("🅿️ Parkplatz FREI (HIGH)");
    }
  }
}
