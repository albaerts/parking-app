// Simple I2C raw register reader for quick ID/debug
// Reads registers 0x00..0x1F from address 0x30 and prints hex
// SDA -> GPIO21, SCL -> GPIO22

#include <Wire.h>

const int I2C_SDA = 21;
const int I2C_SCL = 22;
const uint8_t TARGET_ADDR = 0x30;

void setup() {
  Serial.begin(115200);
  delay(200);
  Wire.begin(I2C_SDA, I2C_SCL);
  Serial.printf("I2C raw reader starting. SDA=%d SCL=%d, addr=0x%02X\n", I2C_SDA, I2C_SCL, TARGET_ADDR);
  delay(100);
}

void dump_range(uint8_t addr, uint8_t start, uint8_t end) {
  Serial.printf("Dumping 0x%02X: 0x%02X..0x%02X\n", addr, start, end);
  for (uint8_t reg = start; reg <= end; ++reg) {
    // write register pointer
    Wire.beginTransmission(addr);
    Wire.write(reg);
    uint8_t txErr = Wire.endTransmission(false); // send restart
    if (txErr != 0) {
      Serial.printf("  reg 0x%02X: TX err %d\n", reg, txErr);
      continue;
    }
    // request one byte
    Wire.requestFrom((int)addr, 1);
    if (Wire.available()) {
      uint8_t b = Wire.read();
      Serial.printf("  reg 0x%02X: 0x%02X\n", reg, b);
    } else {
      Serial.printf("  reg 0x%02X: <no data>\n", reg);
    }
    delay(10);
  }
}

void loop() {
  dump_range(TARGET_ADDR, 0x00, 0x1F);
  // Try block read of first 8 bytes
  Serial.println("Trying block read 0x00..0x07");
  Wire.beginTransmission(TARGET_ADDR);
  Wire.write((uint8_t)0x00);
  if (Wire.endTransmission(false) == 0) {
    Wire.requestFrom((int)TARGET_ADDR, 8);
    int i = 0;
    while (Wire.available()) {
      uint8_t b = Wire.read();
      Serial.printf("  [0x%02X] = 0x%02X\n", i, b);
      i++;
    }
    if (i==0) Serial.println("  block read returned 0 bytes");
  } else {
    Serial.println("  block read: TX error");
  }

  // Read product ID / WHO_AM_I at 0x39 (expected 0x10 for MMC56x3)
  Serial.println("Reading PRODUCT_ID (0x39) and STATUS (0x18)");
  // product id
  Wire.beginTransmission(TARGET_ADDR);
  Wire.write((uint8_t)0x39);
  if (Wire.endTransmission(false) == 0) {
    Wire.requestFrom((int)TARGET_ADDR, 1);
    if (Wire.available()) {
      uint8_t pid = Wire.read();
      Serial.printf(" PRODUCT_ID (0x39) = 0x%02X\n", pid);
    } else Serial.println(" PRODUCT_ID read: no data");
  } else Serial.println(" PRODUCT_ID read: TX error");

  // status reg
  Wire.beginTransmission(TARGET_ADDR);
  Wire.write((uint8_t)0x18);
  if (Wire.endTransmission(false) == 0) {
    Wire.requestFrom((int)TARGET_ADDR, 1);
    if (Wire.available()) {
      uint8_t st = Wire.read();
      Serial.printf(" STATUS (0x18) = 0x%02X\n", st);
    } else Serial.println(" STATUS read: no data");
  } else Serial.println(" STATUS read: TX error");

  Serial.println("Done. Sleeping 10s before next dump...\n");
  delay(10000);
}
