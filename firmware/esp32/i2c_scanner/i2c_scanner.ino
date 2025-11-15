#include <Wire.h>

const int I2C_SDA = 21; // kept for reference (updated)
const int I2C_SCL = 22; // kept for reference (updated)

void setup() {
  Serial.begin(115200);
  delay(200);
  // Use default Wire pins for this board (try board's default SDA/SCL)
  Wire.begin();
  Serial.println("I2C Scanner starting (Wire.begin())...");
}

void loop() {
  Serial.println("Scanning I2C bus...");
  byte error, address;
  int nDevices = 0;
  for(address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("Found device at 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.println(" !");
      nDevices++;
    } else if (error == 4) {
      Serial.print("Unknown error at 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
    }
    delay(5);
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found");
  else {
    Serial.print("done, devices: ");
    Serial.println(nDevices);
  }
  Serial.println("----");
  delay(3000);
}
