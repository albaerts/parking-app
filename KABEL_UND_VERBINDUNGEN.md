# ⚡ **BENÖTIGTE KABEL & VERBINDUNGEN FÜR SMART PARKING BÜGEL**

## 🎯 **KABEL-CHECKLISTE FÜR DEINEN PROTOTYP:**

---

## 📋 **ZWINGEND BENÖTIGTE KABEL:**

### **1. 🔌 JUMPER KABEL SET**
```bash
DIGITEC SUCHE: "Jumper Kabel Set Male Female"
PREIS: CHF 8-12
ANZAHL: 40 Stück (M-M, M-F, F-F)

VERWENDUNG:
✅ Raspberry Pi GPIO → Proto HAT
✅ HAT → LEDs (3x Kabel)
✅ HAT → Servo Motor (3x Kabel)  
✅ HAT → Ultraschallsensor (4x Kabel)
✅ HAT → Widerstände für LEDs

KONKRETE ARTIKEL:
- "Elegoo Jumper Wire 40 STK" - CHF 8
- "Arduino Jumper Kabel Set" - CHF 10
- "Breadboard Jumper Wire Kit" - CHF 12
```

### **2. 🔋 USB-C KABEL (Pi Stromversorgung)**
```bash
DIGITEC SUCHE: "USB-C Kabel 1m"
PREIS: CHF 12-18
LÄNGE: 1-2 Meter

VERWENDUNG:
✅ PowerBank → Raspberry Pi 4 Stromversorgung

KONKRETE ARTIKEL:
- "Anker USB-C Kabel 1.8m" - CHF 15
- "Belkin USB-C Cable 2m" - CHF 18  
- "AmazonBasics USB-C 1m" - CHF 12
```

### **3. 📡 USB VERLÄNGERUNG (4G Stick)**
```bash
DIGITEC SUCHE: "USB 3.0 Verlängerung 1m"
PREIS: CHF 8-12
ZWECK: 4G-Stick optimal positionieren

VERWENDUNG:
✅ Raspberry Pi → 4G USB-Stick
✅ Bessere Signalqualität durch Positionierung

ALTERNATIVE: Direkt einstecken (aber schlechteres Signal)
```

---

## 🛠️ **VERKABELUNGS-PLAN:**

### **RASPBERRY PI GPIO BELEGUNG:**
```bash
SERVO MOTOR:
├─ VCC → 5V (Pin 2)
├─ GND → Ground (Pin 6) 
└─ Signal → GPIO 18 (Pin 12)

LEDs + WIDERSTÄNDE:
├─ Rote LED → GPIO 23 (Pin 16) → 220Ω → GND
├─ Grüne LED → GPIO 24 (Pin 18) → 220Ω → GND
└─ Blaue LED → GPIO 25 (Pin 22) → 220Ω → GND

ULTRASCHALLSENSOR:
├─ VCC → 5V (Pin 4)
├─ GND → Ground (Pin 14)
├─ Trigger → GPIO 20 (Pin 38)
└─ Echo → GPIO 21 (Pin 40)

STROMVERSORGUNG:
├─ PowerBank → USB-C → Raspberry Pi
└─ Pi → USB 3.0 → 4G USB-Stick
```

---

## 🛒 **ERWEITERTE KABEL-LISTE (OPTIONAL):**

### **4. 🌐 ETHERNET KABEL (Backup-Internet)**
```bash
DIGITEC SUCHE: "Ethernet Kabel 2m"
PREIS: CHF 8
ZWECK: Internet-Backup falls 4G ausfällt
```

### **5. 🔗 MICRO-USB KABEL (Servo Backup-Power)**
```bash
PREIS: CHF 5
ZWECK: Falls Servo mehr Strom braucht
NUR BEI PROBLEMEN NÖTIG
```

### **6. 🔧 DUPONT STECKER (Professionell)**
```bash
DIGITEC SUCHE: "Dupont Connector Set"
PREIS: CHF 15
ZWECK: Feste Verbindungen statt Jumper
NUR FÜR FINALE VERSION
```

---

## 💡 **KABEL-EMPFEHLUNGEN FÜR DIGITEC:**

### **🎯 MINIMAL-SET (REICHT FÜR PROTOTYP):**
```bash
1. "Elegoo Jumper Wire 40 STK"      CHF 8
2. "USB-C Kabel 1.8m Anker"        CHF 15
3. "USB 3.0 Verlängerung 1m"       CHF 10

KABEL GESAMT:                       CHF 33
```

### **🚀 KOMPLETT-SET (EMPFOHLEN):**
```bash
1. "Jumper Wire Set M-M/M-F/F-F"    CHF 12
2. "USB-C Kabel 2m Premium"         CHF 18
3. "USB Verlängerung mit LED"       CHF 12
4. "Ethernet Kabel 3m"              CHF 8

KABEL GESAMT:                       CHF 50
```

---

## ⚠️ **HÄUFIGE KABEL-FEHLER VERMEIDEN:**

### **❌ TYPISCHE PROBLEME:**
```bash
1. Zu kurze Kabel → Schlechte Montage
2. Falsche Jumper-Typen → Verbindung unmöglich  
3. Schwaches USB-C Kabel → Pi crasht bei Last
4. 4G-Stick direkt am Pi → Schlechtes Signal
```

### **✅ RICHTIGE VORBEREITUNG:**
```bash
1. Jumper: Male-Female für Pi→HAT
2. USB-C: Mindestens 3A Strombelastung
3. USB-Verlängerung: 4G-Stick optimal platzieren
4. Ersatz-Kabel: Immer 2-3 Jumper mehr bestellen
```

---

## 🎯 **FINALE KABEL-EMPFEHLUNG:**

**BESTELLE ZUSÄTZLICH BEI DIGITEC:**
1. **"Elegoo Jumper Wire 40 STK"** - CHF 8
2. **"Anker USB-C Kabel 1.8m"** - CHF 15  
3. **"USB 3.0 Verlängerung 1m"** - CHF 10

**NEUE GESAMTKOSTEN: CHF 210** (statt CHF 187)

**Mit diesen Kabeln kannst du deinen Smart Parking Bügel komplett verkabeln!** 🚗⚡

---

## 🔍 **DIGITEC SUCHBEGRIFFE:**

```bash
KOPIERE DIESE BEGRIFFE 1:1 IN DIE DIGITEC SUCHE:

1. "Elegoo Jumper Wire"
2. "Anker USB-C Kabel 1.8m" 
3. "USB 3.0 Verlängerungskabel 1m"
4. "Ethernet Kabel Cat6 2m"
```

**Jetzt hast du ALLES für deinen Prototyp!** 🎉
