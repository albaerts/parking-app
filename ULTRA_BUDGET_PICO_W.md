# 💰 **ULTRA-BUDGET SMART PARKING BÜGEL - PICO W VERSION**

## 🎯 **CHF 60 ERSPARNIS MIT RASPBERRY PI PICO W!**

### **📍 DIGITEC.CH - ULTRA-GÜNSTIGE EINKAUFSLISTE:**

---

## 🛒 **1. RASPBERRY PI PICO W** 🔥 **MEGA-GÜNSTIG!**
```bash
SUCHE: "Raspberry Pi Pico W"
PREIS: CHF 10 (statt CHF 70 Pi 4!)
ZWECK: Mikrocontroller für Smart Parking Bügel
EINSPARUNG: CHF 60!
```

## 🛒 **2. POWERBANK** (KLEINER REICHT!)
```bash
SUCHE: "PowerBank 10000mAh USB-C"
PREIS: CHF 35 (statt CHF 70!)
ZWECK: Stromversorgung für Pico W (sehr sparsam)
EINSPARUNG: CHF 35 - Pico W braucht viel weniger Strom!
```

## 🛒 **3. SERVO MOTOR**
```bash
SUCHE: "SG90 Servo 3er Pack"
PREIS: CHF 25
ZWECK: Bewegt den Parkbügel hoch/runter
GLEICH WIE VORHER
```

## 🛒 **4. BREADBOARD** (STATT TEURER HAT)
```bash
SUCHE: "Breadboard 400 Pins + Jumper"
PREIS: CHF 8 (statt CHF 12 HAT)
ZWECK: Verkabelung aller Komponenten
EINSPARUNG: CHF 4 - Pico W braucht keine HAT!
```

## 🛒 **5. LED SET**
```bash
SUCHE: "Joy-it LED Sortiment"
PREIS: CHF 12
ZWECK: Status-Anzeigen (rot/grün/blau)
GLEICH WIE VORHER
```

## 🛒 **6. ULTRASCHALLSENSOR**
```bash
SUCHE: "HC-SR04 Ultraschall Sensor"
PREIS: CHF 5
ZWECK: Erkennt ob Auto im Parkplatz steht
GLEICH WIE VORHER
```

## 🛒 **7. JUMPER KABEL SET**
```bash
SUCHE: "Jumper Kabel Set Male Female"
PREIS: CHF 8
ZWECK: Verbindungen zwischen Pico und Sensoren
GLEICH WIE VORHER
```

## 🛒 **8. MICRO-USB KABEL** (PICO STROMVERSORGUNG)
```bash
SUCHE: "Micro USB Kabel 2A"
PREIS: CHF 8 (statt CHF 12 USB-C)
ZWECK: PowerBank → Pico W Stromversorgung
EINSPARUNG: CHF 4
```

## 🛒 **9. MICRO-SD KARTE** ❌ **NICHT NÖTIG!**
```bash
WEGFALL: Pico W braucht keine SD-Karte!
EINSPARUNG: CHF 13
```

## ❌ **KEIN 4G USB-STICK NÖTIG!**
```bash
WEGFALL: Pico W hat WiFi integriert
EINSPARUNG: CHF 30 - Größte Ersparnis!
```

---

## 💰 **ULTRA-BUDGET GESAMTKOSTEN:**

```bash
✅ Raspberry Pi Pico W               CHF 10  (statt CHF 70)
✅ PowerBank 10000mAh                CHF 35  (statt CHF 70)
✅ SG90 Servo 3er-Pack              CHF 25  (gleich)
✅ Breadboard + Jumper Set           CHF 8   (statt CHF 12)
✅ Joy-it LED Sortiment              CHF 12  (gleich)
✅ HC-SR04 Ultraschallsensor         CHF 5   (gleich)
✅ Jumper Kabel Set extra            CHF 8   (gleich)
✅ Micro USB Kabel                   CHF 8   (statt CHF 12)

ZWISCHENSUMME:                       CHF 111
VERSANDKOSTEN:                       CHF 0 (ab CHF 50)
DIGITEC GESAMT:                      CHF 111
```

---

## 🏗️ **ZUSÄTZLICH BENÖTIGT (BAUMARKT):**

```bash
📍 BAUHAUS ZÜRICH (Hardturmstrasse 133)
✅ Acrylglas Platte 30x21cm, 5mm    CHF 13
✅ M5 Schrauben-Set                  CHF 10

BAUMARKT GESAMT:                     CHF 23
```

---

## 🎯 **ULTRA-BUDGET PROJEKT GESAMTKOSTEN:**

```bash
DIGITEC ELEKTRONIK:     CHF 111
BAUHAUS MECHANIK:       CHF 23
GESAMTPROJEKT:          CHF 134

EINSPARUNG GEGENÜBER ORIGINAL: CHF 76!
```

---

## ⚠️ **WAS ÄNDERT SICH BEI DER SOFTWARE?**

### **🔄 DEINE PARKING_BARRIER.PY ANPASSUNGEN:**

```python
# VORHER (Raspberry Pi 4):
import RPi.GPIO as GPIO
import requests

# NACHHER (Pico W):
import machine
import network
import urequests  # statt requests

# GPIO bleibt fast gleich:
servo = machine.PWM(machine.Pin(18))    # statt GPIO.PWM
red_led = machine.Pin(23, machine.Pin.OUT)  # statt GPIO.setup
green_led = machine.Pin(24, machine.Pin.OUT)

# WiFi Setup (statt 4G):
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("DEIN_WIFI_NAME", "DEIN_WIFI_PASSWORT")

# HTTP Requests:
response = urequests.get("http://dein-backend.com/api")  # statt requests

# Rest der Logik bleibt 95% gleich!
```

### **📝 ANPASSUNG AUFWAND:**
```bash
ÄNDERUNGEN: 10-15 Zeilen Code
AUFWAND: 30-60 Minuten
SCHWIERIGKEIT: Einfach (fast alles gleich)
TUTORIALS: Viele online verfügbar
```

---

## 🚀 **BESTELLUNG IN 3 SCHRITTEN:**

1. **🌐 Gehe auf:** `digitec.ch`
2. **🔍 Suche die 8 Artikel** mit den exakten Begriffen oben
3. **💳 Bezahle mit TWINT** → 1-2 Tage Lieferung

---

## ✅ **WARUM PICO W PERFEKT IST:**

### **🎯 VORTEILE:**
```bash
✅ 87% günstiger! (CHF 10 vs CHF 70)
✅ WiFi integriert - kein 4G-Stick nötig
✅ Ultra-niedriger Stromverbrauch
✅ Kompakt und robust
✅ Python-ähnlich programmierbar
✅ Perfekt für IoT-Projekte
✅ Viele Online-Tutorials
```

### **⚠️ KLEINE NACHTEILE:**
```bash
❌ Nur WiFi (kein 4G) - aber reicht meist!
❌ Weniger RAM - aber genug für Parkbügel
❌ 30 min Code-Anpassung nötig
❌ Kein vollständiges Linux
```

---

## 🏆 **ULTRA-BUDGET FAZIT:**

**CHF 134 STATT CHF 210 - 36% GÜNSTIGER!**

- ✅ **CHF 76 Ersparnis!**
- ✅ **Gleiche Funktionalität**
- ✅ **Noch kompakter & sparsamer**
- ✅ **WiFi reicht für die meisten Standorte**

**Dein Smart Parking Bügel für den Preis eines Abendessens!** 🚗💡💰

---

## 🛒 **SCHNELL-BESTELLUNG LINKS:**

```bash
DIGITEC SUCHBEGRIFFE (COPY & PASTE):
1. "Raspberry Pi Pico W"
2. "PowerBank 10000mAh USB-C PD"  
3. "SG90 Servo 3er Pack Arduino"
4. "Breadboard 400 Pins Jumper Set"
5. "Joy-it LED Sortiment bunt"
6. "HC-SR04 Ultraschallsensor Arduino"
7. "Jumper Wire Male Female 40 STK"
8. "Micro USB Kabel 2A 1m"
```

**BESTELLE HEUTE UND SPARE CHF 76!** 🎉
