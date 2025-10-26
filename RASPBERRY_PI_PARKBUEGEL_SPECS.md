# 🍓 RASPBERRY PI SMART PARKBÜGEL - HARDWARE SPEZIFIKATION

## 🎯 **RASPBERRY PI SETUP**

### **🖥️ HAUPTCONTROLLER:**
```bash
ARTIKEL: Raspberry Pi 4 Model B (4GB RAM)
Technische Daten:
├─ CPU: Quad-Core ARM Cortex-A72 @ 1.5GHz
├─ RAM: 4GB LPDDR4-3200 SDRAM
├─ GPIO: 40 Pins (26 nutzbar)
├─ Connectivity: WiFi 802.11ac + Bluetooth 5.0 + Gigabit Ethernet
├─ USB: 4x USB (2x USB 3.0, 2x USB 2.0)
├─ Power: USB-C 5V 3A
├─ microSD: Klasse 10 (min. 32GB empfohlen)
└─ Betriebstemperatur: 0°C bis +50°C

🛒 BEZUGSQUELLEN:
1️⃣ Reichelt Elektronik
   Part-Number: RPI 4 B 4GB
   Preis: 64.95€ (inkl. 19% MwSt.)
   
2️⃣ Berrybase.de
   Part-Number: RASP-PI-4-4GB
   Preis: 67.90€ (inkl. MwSt.)

💰 GEWÄHLTER PREIS: 64.95€
```

---

## 🔌 **RASPBERRY PI HATs & ERWEITERUNGEN:**

### **📡 4G/LTE KOMMUNIKATION:**
```bash
ARTIKEL: Waveshare SIM7600G-H 4G HAT für Raspberry Pi
Technische Daten:
├─ 4G LTE Cat-4 (Europa-Frequenzen optimiert)
├─ Download: 150 Mbps / Upload: 50 Mbps
├─ GPS/GNSS: Integriert (Multi-Constellation)
├─ Interface: USB + UART (AT Commands)
├─ SIM: Nano-SIM Slot
├─ Antennen: 2x IPEX4 Connector (LTE + GPS)
├─ Power: 5V via Pi, 2A peak current
└─ Direkter Pi-Aufsteckung (HAT-kompatibel)

🛒 BEZUGSQUELLE:
Waveshare Official Store
Part-Number: SIM7600G-H-4G-HAT
Preis: 94.99€ (inkl. MwSt.)

💰 GEWÄHLTER PREIS: 94.99€
```

### **⚡ POWER MANAGEMENT HAT:**
```bash
ARTIKEL: UPS HAT für Raspberry Pi (unterbrechungsfreie Stromversorgung)
Technische Daten:
├─ Batterie: 18650 Li-Ion (2x Slots)
├─ Solar Input: 6-24V DC (MPPT Controller integriert)
├─ Output: 5V 3A für Raspberry Pi
├─ USB-C Power Delivery für Pi
├─ Battery Management System (BMS)
├─ I2C Interface für Monitoring
├─ LED Status-Anzeigen
└─ Schutz: Überspannung, Kurzschluss, Temperatur

🛒 BEZUGSQUELLE:
Waveshare UPS HAT (B)
Part-Number: UPS-HAT-B
Preis: 39.99€

💰 GEWÄHLTER PREIS: 39.99€
```

---

## 🔧 **SENSOREN & AKTUATOREN (GPIO-Anschluss):**

### **🔍 ULTRASCHALL-SENSOR:**
```bash
ARTIKEL: JSN-SR04T Wasserdichter Ultraschallsensor
Technische Daten:
├─ Reichweite: 25cm - 450cm
├─ Genauigkeit: ±1cm
├─ Arbeitsfrequenz: 40kHz
├─ Interface: GPIO (Trigger/Echo)
├─ Power: 3.3V oder 5V
├─ Schutzart: IP67 (vollständig wasserdicht)
└─ Arbeitstemperatur: -10°C bis +70°C

🛒 BEZUGSQUELLE:
Amazon/AliExpress "JSN-SR04T"
Preis: 12.90€

💰 GEWÄHLTER PREIS: 12.90€
```

### **🔒 LINEAR ACTUATOR (Bügelmechanik):**
```bash
ARTIKEL: 12V Linear Actuator 50mm Hub, 100N Kraft
Technische Daten:
├─ Hub: 50mm (ausreichend für Parkbügel)
├─ Kraft: 100N (Push/Pull)
├─ Geschwindigkeit: 10mm/s
├─ Power: 12V DC, 2A max
├─ Duty Cycle: 25% (verhindert Überhitzung)
├─ Schutzart: IP54
├─ Endschalter: Integriert
└─ Befestigung: Clevis-Mount (beide Seiten)

🛒 BEZUGSQUELLE:
Progressive Automations PA-04
Preis: 189.00€ (inkl. Versand)

💰 GEWÄHLTER PREIS: 189.00€
```

### **🔄 RELAIS-MODUL (Actuator Control):**
```bash
ARTIKEL: 2-Kanal Relais-Modul 12V/10A (opto-isoliert)
Technische Daten:
├─ Kanäle: 2 (für Actuator Vor/Zurück)
├─ Schaltleistung: 12V/10A DC
├─ Steuerung: 3.3V GPIO-kompatibel
├─ Optokoppler-Isolation
├─ LED Status-Anzeigen
├─ Schraubklemmen für einfache Verkabelung
└─ Hutschienen-Montage möglich

🛒 BEZUGSQUELLE:
AZDelivery 2-Relais Modul
Preis: 9.49€

💰 GEWÄHLTER PREIS: 9.49€
```

---

## 🔋 **STROMVERSORGUNG (SOLAR + BATTERIE):**

### **☀️ SOLAR PANEL:**
```bash
ARTIKEL: 100W Monokristallines Solar Panel 12V
Technische Daten:
├─ Leistung: 100W (bei 1000W/m² Einstrahlung)
├─ Voltage: 18V (Vmp), 21.6V (Voc)
├─ Current: 5.56A (Imp), 6.11A (Isc)
├─ Effizienz: 20.6% (Monokristallin)
├─ Größe: 1000 x 670 x 35mm
├─ Gewicht: 7.5kg
├─ Rahmen: Eloxiertes Aluminium
├─ Glas: 3.2mm gehärtetes Solarglas
└─ Zertifizierung: TÜV, CE, IEC61215

🛒 BEZUGSQUELLE:
Offgridtec Solar Panel 100W Mono
Preis: 89.90€

💰 GEWÄHLTER PREIS: 89.90€
```

### **🔋 BATTERIE-PACK:**
```bash
ARTIKEL: 2x 18650 Li-Ion Batterien (3500mAh) für UPS HAT
Technische Daten:
├─ Typ: Samsung INR18650-35E (Original)
├─ Kapazität: 3500mAh pro Zelle
├─ Voltage: 3.7V nominal (4.2V max)
├─ Entladestrom: 8A kontinuierlich
├─ Zyklen: >500 (bei 80% Kapazität)
├─ Schutzschaltung: Integriert im Pi UPS HAT
└─ Gesamtkapazität: 7000mAh @ 3.7V = 25.9Wh

🛒 BEZUGSQUELLE:
Akkuteile.de Samsung INR18650-35E
Preis: 6.95€ pro Stück (2x = 13.90€)

💰 GEWÄHLTER PREIS: 13.90€
```

---

## 💳 **KOSTENZUSAMMENFASSUNG:**

```bash
RASPBERRY PI SMART PARKBÜGEL - HARDWARE KOSTEN:

Controller & Computing:               64.95€
├─ Raspberry Pi 4B (4GB)             64.95€

Kommunikation:                        94.99€  
├─ SIM7600G-H 4G HAT                 94.99€

Power Management:                     143.79€
├─ UPS HAT für Pi                    39.99€
├─ 100W Solar Panel                  89.90€
├─ 2x 18650 Batterien                13.90€

Sensoren & Aktuatoren:               211.39€
├─ JSN-SR04T Ultraschallsensor       12.90€
├─ Linear Actuator 12V 100N          189.00€
├─ 2-Kanal Relais Modul              9.49€

Installation & Zubehör:               85.00€
├─ Gehäuse IP65 (groß für Pi+HATs)   45.00€
├─ Verkabelung & Stecker             15.00€
├─ Montage-Hardware                  25.00€

GESAMT-HARDWARE-KOSTEN:              600.12€

Monatliche Betriebskosten:
├─ 4G SIM-Karte (10GB)               15.00€/Monat
├─ Backend-Hosting Anteil            3.00€/Monat
└─ Wartungs-Reserve                  5.00€/Monat
TOTAL OPERATING:                     23.00€/Monat
```

## 🐍 **SOFTWARE-STACK:**
- **OS:** Raspberry Pi OS Lite (64-bit)
- **Sprache:** Python 3.9+ 
- **GPIO:** RPi.GPIO oder gpiozero
- **4G:** ppp0 dialup + AT commands  
- **Backend:** Python FastAPI Client
- **Database:** SQLite lokal + Cloud Sync

Soll ich als nächstes die Python-Software für den Raspberry Pi erstellen? 🍓
