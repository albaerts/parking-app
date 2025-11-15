// I2C health diagnostic for ESP32
//  - reports SDA/SCL levels with FLOAT / PULLUP / PULLDOWN
//  - pulses SCL at multiple speeds while sampling SDA to detect any device activity
//  - runs Wire scan at the end

#include <Wire.h>
#include <Arduino.h>

// Updated per user wiring: SDA -> GPIO21, SCL -> GPIO22
const int SDA_PIN = 21;
const int SCL_PIN = 22;

void read_levels(const char* label) {
  int sda = digitalRead(SDA_PIN);
  int scl = digitalRead(SCL_PIN);
  Serial.printf("%s: SDA=%d SCL=%d\n", label, sda, scl);
}

void pulse_and_sample(unsigned int half_period_us, unsigned int cycles) {
  Serial.printf("Pulsing SCL half_period_us=%d us, cycles=%d\n", half_period_us, cycles);
  int sda_low_count = 0;
  for (unsigned int i=0;i<cycles;i++) {
    // SCL low
    pinMode(SCL_PIN, OUTPUT); digitalWrite(SCL_PIN, LOW);
    delayMicroseconds(half_period_us);
    // release SCL high
    pinMode(SCL_PIN, INPUT_PULLUP);
    delayMicroseconds(half_period_us/2);
    int sda = digitalRead(SDA_PIN);
    if (sda == 0) sda_low_count++;
    delayMicroseconds(half_period_us/2);
  }
  Serial.printf("During pulses, SDA seen LOW %d/%d times\n", sda_low_count, cycles);
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("I2C health probe starting...");
  Serial.printf("Pins: SDA=%d SCL=%d\n", SDA_PIN, SCL_PIN);

  // float (input)
  pinMode(SDA_PIN, INPUT);
  pinMode(SCL_PIN, INPUT);
  delay(20);
  read_levels("FLOAT");

  // internal pullup
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delay(20);
  read_levels("PULLUP");

  // internal pulldown
  pinMode(SDA_PIN, INPUT_PULLDOWN);
  pinMode(SCL_PIN, INPUT_PULLDOWN);
  delay(20);
  read_levels("PULLDOWN");

  // quick low pulse test
  pinMode(SDA_PIN, OUTPUT); digitalWrite(SDA_PIN, LOW);
  pinMode(SCL_PIN, OUTPUT); digitalWrite(SCL_PIN, LOW);
  delay(50);
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delay(20);
  read_levels("After LOW pulse -> PULLUP");

  // sample during pulses (fast, medium, slow)
  pinMode(SDA_PIN, INPUT_PULLUP);
  pulse_and_sample(5, 200);    // ~100 kHz * 200 cycles
  pulse_and_sample(50, 200);   // ~10 kHz
  pulse_and_sample(500, 200);  // ~1 kHz

  // Run Wire scan
  Serial.println("Running Wire scan...");
  Wire.begin(SDA_PIN, SCL_PIN);
  byte found = 0;
  for (byte addr=1; addr<127; addr++) {
    Wire.beginTransmission(addr);
    byte err = Wire.endTransmission();
    if (err == 0) { Serial.printf("Found device at 0x%02X\n", addr); found++; }
  }
  if (found==0) Serial.println("No I2C devices found by Wire scan");
  else Serial.printf("Wire scan found %d device(s)\n", found);

  Serial.println("Diagnostics complete. Sleeping...\n");
}

void loop() {
  delay(10000);
}
