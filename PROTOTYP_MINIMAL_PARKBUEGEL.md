# 🍓 RASPBERRY PI PARKBÜGEL - EINFACHER PROTOTYP

## 🎯 **PROTOTYP-ZIEL: MINIMALER FUNKTIONSFÄHIGER AUFBAU**

### **✅ KERN-FUNKTIONEN:**
- **📱 SIM-Karte** für Internetverbindung
- **🔋 Batterie** für Stromversorgung  
- **⬆️⬇️ Bügel hoch/runter** (Mini-Stange als Proof-of-Concept)
- **🛠️ Montierboard** für einfache Verkabelung
- **🐍 Python Software** für Steuerung

---

## 🛒 **MINIMALSTE HARDWARE-LISTE (PROTOTYP)**

### **🖥️ 1. RASPBERRY PI (CONTROLLER):**
```bash
ARTIKEL: Raspberry Pi 4 Model B (2GB RAM) - REICHT FÜR PROTOTYP
Preis: 54.95€ (Reichelt)
Begründung: 2GB RAM völlig ausreichend für unsere Anwendung
```

### **📡 2. SIM-KARTE LÖSUNG (EINFACHSTE VARIANTE):**
```bash
ARTIKEL: Huawei E3372 4G USB Stick (entsperrt)
Preis: 29.90€ (Amazon)
Vorteile:
├─ Plug & Play am Pi via USB
├─ Nano-SIM Slot integriert
├─ Keine zusätzliche HAT nötig
├─ Funktioniert sofort mit Linux
└─ Bewährte Lösung

SIM-KARTE:
├─ Telekom MagentaMobil Prepaid
├─ 10GB/Monat für 9.95€
└─ Oder: Congstar Prepaid 15€/Monat
```

### **🔋 3. BATTERIE (EINFACHSTE LÖSUNG):**
```bash
ARTIKEL: Anker PowerCore 26800 mAh Power Bank
Preis: 59.99€ (Amazon)
Vorteile:
├─ USB-C Output für Pi (5V/3A)
├─ 26.8Ah = ~20 Stunden Pi-Betrieb
├─ Fertige Lösung, keine Verkabelung
├─ Ladeanzeige integriert
└─ Wetterfest (IP67 Version verfügbar)

ALTERNATIVE (noch einfacher):
Powerbank mit Solar-Panel integriert
Preis: 39.99€ (für Prototyp völlig OK)
```

### **🔒 4. MINI-PARKBÜGEL (PROTOTYP-MECHANIK):**
```bash
ARTIKEL: Micro Servo SG90 + 3D-gedruckter Arm
Preis: 4.99€ (Servo) + 0€ (3D-Druck)

SERVO-SPECS:
├─ Drehmoment: 1.8kg/cm (reicht für Mini-Stange)
├─ Drehwinkel: 180° (0° = unten, 90° = hoch)
├─ Power: 5V (direkt vom Pi)
├─ Steuerung: PWM Signal (1 GPIO Pin)
└─ Größe: 23 x 12 x 29mm

MINI-BÜGEL-AUFBAU:
├─ Servo-Arm (im Lieferumfang)
├─ 10cm Holzstab oder Kunststoffstange
├─ Heißkleber für Befestigung
└─ Fertig ist der Prototyp-Bügel!

💡 PROTOTYP-IDEE: 10cm Stange die sich von horizontal (frei) 
   auf vertikal (blockiert) dreht. Symbolischer Parkbügel!
```

### **🛠️ 5. MONTIERBOARD & VERKABELUNG:**
```bash
ARTIKEL: Breadboard + Pi-Cobbler Kit
Preis: 19.90€ (AZDelivery)

SET ENTHÄLT:
├─ Half-Size Breadboard (400 Pins)
├─ GPIO Cobbler (40-Pin auf Breadboard)
├─ Flachbandkabel 40-polig
├─ Jumper-Kabel Set (Male/Male, Male/Female)
└─ Widerstand-Set (220Ω für LEDs etc.)

VORTEILE:
├─ Kein Löten nötig
├─ Schnelle Prototyp-Verkabelung
├─ Einfach zu ändern/debuggen
├─ Alle GPIO-Pins verfügbar
└─ Ideale Prototyp-Plattform
```

### **💡 6. STATUS-LEDs (Optional aber hilfreich):**
```bash
ARTIKEL: LED-Set (Rot/Grün/Blau) mit Widerständen
Preis: 5.99€ (Amazon)

STATUS-ANZEIGEN:
├─ GRÜN: System läuft, Verbindung OK
├─ ROT: Fehler oder Wartung
├─ BLAU: Bügel in Bewegung
└─ Blinken: Verschiedene Status-Codes
```

---

## 💰 **PROTOTYP-KOSTEN (MINIMAL):**

```bash
🍓 RASPBERRY PI PARKBÜGEL - PROTOTYP KOSTEN:

Hardware:
├─ Raspberry Pi 4B (2GB)             54.95€
├─ MicroSD Karte 32GB                8.99€
├─ Huawei E3372 4G USB Stick         29.90€
├─ Anker PowerBank 26800mAh          59.99€
├─ Micro Servo SG90                  4.99€
├─ Breadboard + GPIO Cobbler Kit     19.90€
├─ LED Status Set                    5.99€
├─ Mini-Stange (Holz/Kunststoff)     2.00€

GESAMT HARDWARE:                     186.71€

Laufende Kosten:
├─ SIM-Karte (Congstar 10GB)        15.00€/Monat
└─ Backup/Cloud (optional)          3.00€/Monat
TOTAL MONTHLY:                       18.00€/Monat

🎯 PROTOTYP TOTAL: Unter 200€ für voll funktionsfähigen Test!
```

---

## 🔌 **SUPER-EINFACHE VERKABELUNG:**

```bash
GPIO-VERBINDUNGEN (nur 4 Kabel nötig!):

Servo SG90:
├─ VCC (Rot)    → Pi Pin 2 (5V)
├─ GND (Braun)  → Pi Pin 6 (GND)  
└─ Signal (Orange) → Pi Pin 12 (GPIO18 - PWM)

Status-LED (Grün):
├─ Anode (+)    → Pi Pin 16 (GPIO23)
└─ Kathode (-)  → 220Ω Widerstand → GND

USB 4G Stick:
└─ Einfach in USB-Port stecken

Power Bank:
└─ USB-C Kabel zum Pi

FERTIG! Nur 6 Verbindungen total.
```

---

## 🐍 **PYTHON SOFTWARE (ULTRA-EINFACH):**

```python
# parking_prototype.py - Minimaler Parkbügel Controller

import RPi.GPIO as GPIO
import time
import requests
import json
from threading import Thread

# GPIO Setup  
SERVO_PIN = 18        # PWM für Servo
STATUS_LED = 23       # Status LED

# Servo Positionen
POSITION_DOWN = 2.5   # 0° - Bügel unten (frei)
POSITION_UP = 12.5    # 180° - Bügel hoch (blockiert)

class ParkingBarrier:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        GPIO.setup(STATUS_LED, GPIO.OUT)
        
        self.servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM
        self.servo.start(0)
        
        self.is_up = False
        self.device_id = "PROTOTYPE_001"
        
    def move_barrier_up(self):
        """Bügel hochfahren (blockieren)"""
        print("🔒 Bügel wird hochgefahren...")
        self.servo.ChangeDutyCycle(POSITION_UP)
        time.sleep(1)
        self.servo.ChangeDutyCycle(0)  # Signal stoppen
        self.is_up = True
        self.blink_led(3)  # 3x blinken = hoch
        
    def move_barrier_down(self):
        """Bügel runterfahren (freigeben)"""  
        print("🔓 Bügel wird runtergefahren...")
        self.servo.ChangeDutyCycle(POSITION_DOWN)
        time.sleep(1) 
        self.servo.ChangeDutyCycle(0)
        self.is_up = False
        self.blink_led(1)  # 1x blinken = runter
        
    def blink_led(self, times):
        """Status LED blinken lassen"""
        for _ in range(times):
            GPIO.output(STATUS_LED, GPIO.HIGH)
            time.sleep(0.3)
            GPIO.output(STATUS_LED, GPIO.LOW) 
            time.sleep(0.3)
            
    def check_server_commands(self):
        """Server nach Befehlen abfragen"""
        try:
            # Hier würde die Verbindung zu deiner FastAPI laufen
            response = requests.get(
                f"http://deine-api.com/barrier/{self.device_id}/command",
                timeout=10
            )
            
            if response.status_code == 200:
                command = response.json().get('command')
                
                if command == 'UP' and not self.is_up:
                    self.move_barrier_up()
                elif command == 'DOWN' and self.is_up:
                    self.move_barrier_down()
                    
        except Exception as e:
            print(f"❌ Server-Verbindung fehlgeschlagen: {e}")
            
    def run(self):
        """Hauptschleife"""
        print("🚀 Parkbügel Prototyp gestartet!")
        GPIO.output(STATUS_LED, GPIO.HIGH)  # LED an = System läuft
        
        try:
            while True:
                self.check_server_commands()
                time.sleep(5)  # Alle 5 Sekunden Server abfragen
                
        except KeyboardInterrupt:
            print("\n🛑 Prototyp gestoppt")
            
        finally:
            self.servo.stop()
            GPIO.cleanup()

if __name__ == "__main__":
    barrier = ParkingBarrier()
    barrier.run()
```

---

## 📦 **AUFBAU-ANLEITUNG (30 Minuten):**

### **1️⃣ Raspberry Pi vorbereiten:**
```bash
1. Raspberry Pi OS Lite auf SD-Karte flashen
2. SSH aktivieren (ssh file auf Boot-Partition) 
3. Pi booten, via SSH verbinden
4. 4G USB Stick einstecken → sollte automatisch erkannt werden
```

### **2️⃣ Hardware verkabeln:**
```bash
1. GPIO Cobbler auf Breadboard stecken
2. Servo: Rot→5V, Braun→GND, Orange→GPIO18
3. LED: Anode→GPIO23, Kathode→Widerstand→GND
4. Power Bank per USB-C an Pi anschließen
```

### **3️⃣ Software installieren:**
```bash
sudo apt update && sudo apt install python3-pip
pip3 install RPi.GPIO requests
python3 parking_prototype.py
```

**🎉 FERTIG! Prototyp läuft in unter 1 Stunde!**

Soll ich dieses minimal Setup als Basis nehmen und eine detaillierte Schritt-für-Schritt Anleitung erstellen? 🛠️
