// Bit-bang I2C ACK probe for ESP32
// Tests ACK response by manually generating start, writing address and sampling ACK

#include <Arduino.h>

// Updated per user wiring: SDA -> GPIO21, SCL -> GPIO22
const int SDA_PIN = 21;
const int SCL_PIN = 22;

void lineHigh(int pin) { pinMode(pin, INPUT_PULLUP); }
void lineLow(int pin)  { pinMode(pin, OUTPUT); digitalWrite(pin, LOW); }

void i2c_delay_us(unsigned int us) { delayMicroseconds(us); }

void i2c_start() {
  lineHigh(SDA_PIN); lineHigh(SCL_PIN);
  i2c_delay_us(5);
  lineLow(SDA_PIN);
  i2c_delay_us(5);
  lineLow(SCL_PIN);
}

void i2c_stop() {
  lineLow(SDA_PIN);
  i2c_delay_us(5);
  lineHigh(SCL_PIN);
  i2c_delay_us(5);
  lineHigh(SDA_PIN);
  i2c_delay_us(5);
}

bool i2c_write_byte(uint8_t b, unsigned int half_period_us) {
  for (int i = 7; i >= 0; --i) {
    if (b & (1 << i)) lineHigh(SDA_PIN); else lineLow(SDA_PIN);
    i2c_delay_us(half_period_us);
    lineHigh(SCL_PIN);
    i2c_delay_us(half_period_us);
    lineLow(SCL_PIN);
    i2c_delay_us(1);
  }
  // ACK bit: release SDA and sample
  lineHigh(SDA_PIN);
  i2c_delay_us(half_period_us);
  lineHigh(SCL_PIN);
  i2c_delay_us(half_period_us/2);
  int ack = digitalRead(SDA_PIN); // 0 = ACK
  i2c_delay_us(half_period_us/2);
  lineLow(SCL_PIN);
  i2c_delay_us(1);
  return (ack == 0);
}

void test_speed(unsigned int half_period_us) {
  Serial.printf("\nTesting half_period_us=%d (clock ~%d kHz)\n", half_period_us, 1000000/(half_period_us*2));
  int found = 0;
  for (uint8_t addr = 1; addr < 127; ++addr) {
    i2c_start();
    bool ack = i2c_write_byte((addr << 1) | 0, half_period_us);
    i2c_stop();
    if (ack) {
      Serial.printf(" ACK from 0x%02X\n", addr);
      found++;
    }
    delay(2);
  }
  if (!found) Serial.println(" No ACKs detected at this speed.");
  else Serial.printf(" Total %d ACKs detected.\n", found);
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("Bit-bang I2C ACK probe starting...");
  Serial.printf("SDA=%d SCL=%d\n", SDA_PIN, SCL_PIN);
  // Ensure lines idle high
  lineHigh(SDA_PIN); lineHigh(SCL_PIN);
  delay(50);
}

void loop() {
  // test multiple speeds
  test_speed(5);    // ~100 kHz
  test_speed(50);   // ~10 kHz
  test_speed(500);  // ~1 kHz (slow)
  Serial.println("Probe cycle done. Sleeping 5s before repeating...\n");
  delay(5000);
}
