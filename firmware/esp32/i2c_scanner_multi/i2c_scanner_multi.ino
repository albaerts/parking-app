#include <Wire.h>

struct PinPair { int sda; int scl; };

PinPair pairs[] = {
  // common default and alternate pairs
  {21,22}, {22,21}, // default I2C
  {32,33}, {33,32}, // user-wired pair
  {18,19}, {19,18}, // alternate
  {4,5},   {5,4},   // often used on some devboards
  {25,26}, {26,25}, // safe GPIOs
  {16,17}, {17,16}  // additional alternates
};

void scanOnce() {
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
    }
    delay(3);
  }
  if (nDevices == 0) Serial.println("No I2C devices found");
  else {
    Serial.print("done, devices: "); Serial.println(nDevices);
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("Multi I2C scanner starting...");
}

void loop() {
  for (int i=0;i< (int)(sizeof(pairs)/sizeof(pairs[0])); i++) {
    int sda = pairs[i].sda;
    int scl = pairs[i].scl;
    Serial.println("---------------------------");
    Serial.print("Trying SDA="); Serial.print(sda);
    Serial.print(" SCL="); Serial.println(scl);
    Wire.begin(sda, scl);
    delay(50);
    Serial.println("Scanning I2C bus...");
    scanOnce();
    delay(500);
  }
  Serial.println("All pairs tested, sleeping 5s before repeating...");
  delay(5000);
}
