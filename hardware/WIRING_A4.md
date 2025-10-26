# 🧩 Verdrahtung (A4) – ESP32 Smart Parking Prototyp

Komponenten: ESP32 Dev Board, SG92R Micro Servo, Hall-Sensor A3144, Pololu S13V20F5, 2×18650, Breadboard, Dupont-Kabel

---

## 1) Stromversorgung
- 2× 18650 (in Reihe) → Pololu S13V20F5 (Step-Up/Down auf 5.0 V)
- Gemeinsame Masse: GND aller Module verbinden (Pololu/ESP32/Servo/Sensor)
- ESP32: 5V vom Pololu → VIN/5V-Pin, GND → GND
- Servo: 5V (Pololu) → Rot, GND → Braun, Signal → Orange
- Hall-Sensor: 3.3V (ESP32) → VCC, GND → GND, OUT → GPIO 19
- 10 kΩ Pull-up: OUT → 3.3V (falls Modul keinen Pull-up hat)

Sicherheit:
- Polung der 18650 prüfen (geschützte Zellen verwenden)
- Spannung am Pololu (5.0 V) vor dem Anschließen messen

---

## 2) Pinbelegung (ESP32)
- SERVO_PIN: GPIO 18 (PWM)
- HALL_PIN: GPIO 19 (Digital IN, INPUT_PULLUP)
- LED_PIN: GPIO 2 (On-Board LED / Status)

---

## 3) Farbcodes (Empfehlung)
- Rot: +5V
- Orange: Servosignal
- Schwarz: GND
- Grün: Hall OUT
- Gelb: 3.3V
- Blau: Status-LED

---

## 4) ASCII-Layout (Breadboard Skizze)
```
[18650 x2]  ->  Pololu S13V20F5  ->  +5V Rail ---------------> Servo (+)
                                 ->  GND Rail ---------------> Servo (GND)
                                                        \----> ESP32 GND
ESP32 VIN/5V  <------------------------------------------+5V Rail
ESP32 3.3V    ------------------------------------------> Hall VCC
ESP32 GPIO19  ------------------------------------------> Hall OUT
ESP32 GPIO18  ------------------------------------------> Servo Signal
ESP32 GPIO2   ------------------------------------------> Status LED (falls extern)
```

---

## 5) Prüfreihenfolge
1) 5.0 V am Pololu messen
2) ESP32 via USB verbinden (IDE/Seriell prüfen)
3) Servo-Test sketchen → Bewegung ok?
4) Hall-Test sketchen → Magnet LOW/FREE erkennen
5) All-in-One flashen → Bügel folgt Sensor

---

## 6) Hinweise
- SG92R unter Last: eigene 5V-Schiene (Pololu) nutzen, nicht vom 3.3V des ESP32
- Gemeinsamer GND ist Pflicht
- Hall-Sensor entprellen (Software) und Pull-up sicherstellen
