#include <ESP32Servo.h>

// Standard-Testpin: hier auf 13 gesetzt, damit du direkt am GPIO13 testen kannst.
#define SERVO_PIN 13
Servo parkingBarrier;

void setup() {
  Serial.begin(115200);
  parkingBarrier.attach(SERVO_PIN);
  Serial.print("Servo-Test gestartet. Aktueller Servo-Pin: ");
  Serial.println(SERVO_PIN);
  Serial.println("Optional: per Seriell 'pin=<gpio>' senden, um zur Laufzeit umzustecken (Enter am Ende).");
}

void loop() {
  // Optional: zur Laufzeit den Servopin wechseln (z.B. 'pin=18' + Enter)
  static String line;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c != '\n') { line += c; continue; }
    line.trim();
    if (line.startsWith("pin=")) {
      int newPin = line.substring(4).toInt();
      if (newPin > 0) {
        parkingBarrier.detach();
        delay(20);
        parkingBarrier.attach(newPin);
        Serial.print("Servo auf neuen Pin umgehängt: ");
        Serial.println(newPin);
        // kleiner Funktionstest
        parkingBarrier.write(0); delay(500);
        parkingBarrier.write(90); delay(500);
        parkingBarrier.write(45); delay(300);
      } else {
        Serial.println("Ungültiger Pin-Wert");
      }
    } else if (line.length() > 0) {
      Serial.println("Befehl unbekannt. Beispiel: pin=18");
    }
    line = "";
  }

  Serial.println("Bügel runter (0°)");
  parkingBarrier.write(0);
  delay(1500);

  Serial.println("Halteposition (45°)");
  parkingBarrier.write(45);
  delay(1500);

  Serial.println("Bügel hoch (90°)");
  parkingBarrier.write(90);
  delay(1500);
}
