// I2C probe for ESP32 — checks pullups, bus idle level and performs extended scan
// Connect your sensor: SDA -> pin 32, SCL -> pin 33 (adjust pins below if needed)

#include <Wire.h>

// Updated per user wiring: SDA -> GPIO21, SCL -> GPIO22
const int SDA_PIN = 21;
const int SCL_PIN = 22;

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("I2C probe starting...");
  Serial.printf("Using SDA=%d SCL=%d\n", SDA_PIN, SCL_PIN);
}

void loop() {
  Serial.println("--- Bus idle/pullup test ---");
  // enable internal pullups and read lines
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delay(10);
  int sda = digitalRead(SDA_PIN);
  int scl = digitalRead(SCL_PIN);
  Serial.printf("digitalRead (INPUT_PULLUP): SDA=%d SCL=%d (1==HIGH)\n", sda, scl);

  // drive lines low briefly to detect shorts
  Serial.println("Drive lines LOW momentarily to test for shorts...");
  pinMode(SDA_PIN, OUTPUT);
  pinMode(SCL_PIN, OUTPUT);
  digitalWrite(SDA_PIN, LOW);
  digitalWrite(SCL_PIN, LOW);
  delay(50);

  // release lines and check if they go high (pullups present)
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delay(10);
  sda = digitalRead(SDA_PIN);
  scl = digitalRead(SCL_PIN);
  Serial.printf("After LOW pulse: SDA=%d SCL=%d\n", sda, scl);

  // Begin Wire I2C on specified pins and run scan
  Serial.println("--- I2C scan (Wire) ---");
  Wire.begin(SDA_PIN, SCL_PIN);
  byte found = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
      Serial.printf("Found device at 0x%02X\n", addr);
      found++;
      // try to read one byte (non-intrusive if device responds)
      Wire.requestFrom((int)addr, 1);
      if (Wire.available()) {
        uint8_t b = Wire.read();
        Serial.printf(" Read byte 0x%02X from 0x%02X\n", b, addr);
      } else {
        Serial.printf(" No data read from 0x%02X (requestFrom empty)\n", addr);
      }
    } else if (err == 4) {
      Serial.printf("Unknown error at 0x%02X\n", addr);
    }
  }
  if (found == 0) Serial.println("No I2C devices found");
  else Serial.printf("Total %d devices found\n", found);

  Serial.println("--- End probe cycle. Sleeping 5s before repeating... ---\n");
  delay(5000);
}
