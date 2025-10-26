# 🛒 SMART PARKING HARDWARE - KOMPLETTE EINKAUFSLISTE

## 🎯 **PROJEKT-ÜBERSICHT**
**Ziel:** Parkplätze mit IoT-Hardware ausstatten für automatische Belegungserkennung und elektrische Bügel-Steuerung
**Budget pro Parkplatz:** ~630€ (Hardware + Installation)
**ROI:** 17.5 Monate Amortisation

---

## 🧠 **HAUPTCONTROLLER & KOMMUNIKATION**

### **Mikrocontroller:**
- **ESP32-S3 Development Board** - 25€
  - Dual-Core, WiFi + Bluetooth
  - Viel Speicher für komplexe Anwendungen
  - 🛒 *Quelle: AZ-Delivery, Berrybase*

### **Mobilfunk-Modul:**
- **SIM7600E-H 4G LTE Modul** - 45€
  - 4G/LTE + GPS integriert
  - Unterstützt eSIM
  - Weltweite Frequenzen
  - 🛒 *Quelle: Waveshare, Amazon*

### **SIM-Karte & Tarif:**
- **Nano-SIM IoT-Tarif** - 5€/Monat
  - **Empfohlen:** 1NCE (500MB für 10 Jahre ~10€)
  - **Alternative:** Telekom IoT (1MB/Monat ~2€)
  - **Alternative:** Vodafone IoT (2MB/Monat ~3€)
  - 🛒 *Quelle: 1nce.com, Telekom Business*

---

## 🔋 **POWER-MANAGEMENT & SOLAR**

### **Solar-System:**
- **Solar Panel 20W (12V)** - 35€
  - Monokristallin für hohe Effizienz
  - Wetterfest IP65
  - Inklusive MC4-Stecker
  - 🛒 *Quelle: Offgridtec, Amazon*

### **Akku-System:**
- **LiFePO4 Akku 12V 20Ah** - 120€
  - Langlebig, 2000+ Ladezyklen
  - Temperaturesistent (-20°C bis +60°C)
  - Integriertes BMS (Battery Management System)
  - 🛒 *Quelle: Victron Energy, LiTime*

### **Laderegler:**
- **Solar Charge Controller MPPT 10A** - 25€
  - Maximiert Solar-Effizienz
  - Überladungsschutz
  - LCD-Display für Monitoring
  - 🛒 *Quelle: Victron, Renogy*

### **Spannungsversorgung:**
- **DC-DC Converter 12V→5V/3.3V** - 8€
  - Hoher Wirkungsgrad (>90%)
  - 3A Ausgangsstrom
  - Überspannungsschutz
  - 🛒 *Quelle: Pololu, Amazon*

---

## 📊 **SENSOREN FÜR BELEGUNGSERKENNUNG**

### **Haupt-Sensor:**
- **Ultraschall Sensor JSN-SR04T** - 12€
  - Wasserdicht IP67
  - Reichweite: 25cm - 4.5m
  - Auflösung: 1mm
  - 🛒 *Quelle: AZ-Delivery, DFRobot*

### **Backup-Sensoren:**
- **Magnetfeld Sensor (Alternative)** - 15€
  - Detektiert Metall (Auto-Chassis)
  - Sehr niedriger Stromverbrauch
  - Unempfindlich gegen Wetter
  - 🛒 *Quelle: Sensirion, Bosch*

- **PIR Motion Sensor** - 8€
  - Bewegungserkennung als Validierung
  - Großer Erfassungswinkel
  - Einstellbare Empfindlichkeit
  - 🛒 *Quelle: HC-SR501, Amazon*

---

## ⚡ **ELEKTRISCHER BÜGEL-MECHANISMUS**

### **Linear-Antrieb:**
- **Linear Actuator 12V 200mm Hub** - 85€
  - 1000N Schubkraft (100kg)
  - IP65 wasserdicht
  - Endschalter integriert
  - Selbsthemmend bei Stromausfall
  - 🛒 *Quelle: Progressive Automations, TiMOTION*

### **Steuerelektronik:**
- **Relay Module 12V 30A** - 12€
  - Doppel-Relais für Vor/Rückwärts
  - Optokoppler-Isolation
  - LED-Anzeigen für Status
  - 🛒 *Quelle: Elegoo, Amazon*

### **Sicherheits-Komponenten:**
- **Limit Switches (2 Stück)** - 8€
  - Endpositionen oben/unten
  - Wasserdicht IP67
  - NO/NC Kontakte
  - 🛒 *Quelle: Omron, Schneider*

- **Emergency Stop Button** - 15€
  - Mechanische Not-Aus Funktion
  - Für Wartung/Notfälle
  - Pilz-Kopf, drehbar entriegelbar
  - 🛒 *Quelle: Siemens, ABB*

---

## 🏠 **GEHÄUSE & MONTAGE**

### **Elektronik-Gehäuse:**
- **IP65 Gehäuse (300x200x150mm)** - 45€
  - Wetterfest für alle Elektronik
  - Transparenter Deckel (optional)
  - Montage-Flansche integriert
  - 🛒 *Quelle: Fibox, Spelsberg*

### **Mechanische Komponenten:**
- **Metall-Bügel (Edelstahl)** - 60€
  - Custom-Fertigung oder fertig kaufen
  - 40mm Rohr-Durchmesser
  - 80cm Höhe über Boden
  - 🛒 *Quelle: Lokaler Metallbauer, eBay*

### **Befestigung:**
- **4x M8 Bodendübel + Schrauben** - 20€
  - Rostfreier Stahl A4
  - Chemie-Anker für festes Fundament
  - 15cm Verankerungstiefe
  - 🛒 *Quelle: Fischer, Würth*

- **Kabeldurchführungen PG7** - 8€
  - Wasserdichte Kabeleinführung
  - Zugentlastung
  - UV-beständig
  - 🛒 *Quelle: Wiska, Lapp*

---

## 🔌 **VERKABELUNG & KLEINTEILE**

### **Kabel & Leitungen:**
- **10m Kabel 2.5mm² (12V Hauptversorgung)** - 15€
  - Doppelt isoliert
  - UV-beständig für Außenbereich
  - Schwarz/Rot markiert
  - 🛒 *Quelle: Lapp, Ölflex*

- **5m Kabel 0.75mm² (Signalleitungen)** - 8€
  - Geschirmtes Kabel für Sensoren
  - Mehrfarbig (8 Adern)
  - Flexibel verlegbar
  - 🛒 *Quelle: Lapp, Amazon*

### **Verbinder & Kleinteile:**
- **20x Dupont Connectors** - 5€
  - Für Breadboard-Verbindungen
  - Male/Female Sets
  - 2.54mm Pitch
  - 🛒 *Quelle: Amazon, AZ-Delivery*

- **10x Schrumpfschläuche** - 3€
  - Verschiedene Durchmesser
  - 2:1 Schrumpfverhältnis
  - Wasserdicht nach Schrumpfung
  - 🛒 *Quelle: Amazon, Conrad*

- **1x Breadboard + Jumper Wires** - 10€
  - Für Prototyping und Tests
  - 830 Kontakte
  - Verschiedene Kabel-Längen
  - 🛒 *Quelle: Arduino, Elegoo*

### **Elektronik-Bauteile:**
- **5x 10kΩ Widerstände** - 2€
  - Pull-up für Endschalter
  - 1/4W Metallfilm
  - 1% Toleranz
  - 🛒 *Quelle: Reichelt, Conrad*

- **Optional, empfohlen – Pufferkondensatoren**
  - 1× 1000 µF / 16–25 V Elko, Low‑ESR (für SIM7600 HAT)
  - 1× 330 µF / 16–25 V Elko (für Servo)
  - 2× 100 nF Keramik/MLCC, 50 V (parallel zu den Elkos)
  - Zweck: Puffern von Stromspitzen (LTE‑Burst, Servo‑Anlauf), verhindert Spannungseinbrüche
  - 🛒 *Quelle: Reichelt, Farnell, Conrad*

---

## 🛠️ **WERKZEUG (falls nicht vorhanden)**

### **Elektronik-Werkzeug:**
- **Lötkolben + Lötzinn** - 25€
  - 40W Lötkolben mit Temperaturregelung
  - Bleifreies Lötzinn 0.8mm
  - Löt-Station von Weller empfohlen
  - 🛒 *Quelle: Weller, Amazon*

- **Crimping Tool** - 15€
  - Für Dupont-Stecker
  - Verschiedene Crimper-Einsätze
  - Ratschenmechanismus
  - 🛒 *Quelle: Engineer, Amazon*

- **Multimeter** - 20€
  - Digital-Multimeter
  - AC/DC Spannung und Strom
  - Kontinuitätsprüfung
  - 🛒 *Quelle: Fluke, UNI-T*

### **Montage-Werkzeug:**
- **Akkuschrauber** - 40€
  - 18V Li-Ion Akku
  - Drehmoment einstellbar
  - Bits-Set inklusive
  - 🛒 *Quelle: Bosch, Makita*

- **Steinbohrer 8mm** - 8€
  - SDS-Plus Aufnahme
  - Für Beton/Mauerwerk
  - Hartmetall-Spitze
  - 🛒 *Quelle: Bosch, Hilti*

---

## 💰 **KOSTEN-ZUSAMMENFASSUNG**

### **Hardware pro Parkplatz:**
```
Controller & Kommunikation:     70€
Power-System (Solar/Akku):     180€
Sensoren & Elektronik:         35€
Bügel-Mechanismus:            115€
Gehäuse & Montage:             75€
Verkabelung & Kleinteile:      35€
--------------------------------
Subtotal Hardware:            510€

Installation & Arbeitszeit:   120€
--------------------------------
GESAMT PRO PARKPLATZ:         630€
```

### **Werkzeug (einmalig):**
```
Elektronik-Werkzeug:          60€
Montage-Werkzeug:             48€
--------------------------------
Werkzeug gesamt:             108€
```

### **Laufende Kosten (monatlich):**
```
SIM-Karte IoT-Tarif:          3€
Wartung (anteilig):           10€
Strom (minimal):               1€
--------------------------------
Laufende Kosten:              14€
```

---

## 🛒 **BESTELLREIHENFOLGE & LIEFERANTEN**

### **1. Priorität - Lange Lieferzeiten:**
```
✅ Linear Actuator (2-3 Wochen)
✅ LiFePO4 Akku (1-2 Wochen)  
✅ Solar Panel (1-2 Wochen)
✅ IP65 Gehäuse (1-2 Wochen)
```

### **2. Standard-Elektronik:**
```
✅ ESP32-S3 (Amazon Prime)
✅ SIM7600E (Amazon/Waveshare)
✅ Sensoren (Amazon Prime)
✅ Kleinteile (Amazon Prime)
```

### **3. Lokale Beschaffung:**
```
✅ Metall-Bügel (Metallbauer)
✅ Bodendübel (Baumarkt)
✅ Kabel (Elektro-Großhandel)
```

### **💡 Empfohlene Lieferanten:**

**🌐 Online:**
- **Amazon** - Schnelle Lieferung, Standard-Elektronik
- **AZ-Delivery** - ESP32 & Arduino-Komponenten
- **Waveshare** - SIM-Module & Sensoren
- **Offgridtec** - Solar-Komponenten

**🏪 Fachhandel:**
- **Conrad/Reichelt** - Elektronik-Bauteile
- **Würth/Fischer** - Befestigungstechnik
- **Lokaler Metallbauer** - Custom Bügel-Fertigung

**📞 Business-Kontakte:**
- **1NCE** - IoT-SIM-Karten (business@1nce.com)
- **Victron Energy** - Solar-Laderegler
- **Progressive Automations** - Linear-Aktuatoren

---

## ✅ **CHECKLISTE VOR BESTELLUNG**

### **Technische Vorab-Klärung:**
- [ ] API-Endpoint der App verfügbar?
- [ ] Mobilfunk-Empfang am Installationsort?
- [ ] Genehmigung für Bohrungen vorhanden?
- [ ] Stromanschluss für Notfall verfügbar?

### **Standort-spezifische Anpassungen:**
- [ ] Device-ID pro Parkplatz festgelegt
- [ ] Spot-ID in Backend konfiguriert
- [ ] APN des SIM-Providers ermittelt
- [ ] Koordinaten der Parkplätze vermessen

### **Rechtliche Absicherung:**
- [ ] Haftpflichtversicherung informiert
- [ ] CE-Kennzeichnung der Hardware geprüft
- [ ] Datenschutz (DSGVO) beachtet
- [ ] Wartungsvertrag vorbereitet

---

## 🎯 **ROI-BERECHNUNG**

### **Investition pro Parkplatz:**
```
Hardware + Installation: 630€ einmalig
Laufende Kosten: 14€/Monat
```

### **Erwartete Einnahmen:**
```
Konservativ: 50€/Monat pro Parkplatz
Optimistisch: 80€/Monat pro Parkplatz
```

### **Amortisation:**
```
Bei 50€/Monat: 630€ ÷ 36€ = 17.5 Monate
Bei 80€/Monat: 630€ ÷ 66€ = 9.5 Monate
```

### **Gewinn nach 2 Jahren:**
```
Konservativ: (36€ × 24) - 630€ = +234€
Optimistisch: (66€ × 24) - 630€ = +954€
```

---

## 📞 **SUPPORT & KONTAKT**

Bei Fragen zur Hardware-Auswahl:
- **Technischer Support:** Dokumentation im GitHub Repository
- **Hardware-Probleme:** Community Forum
- **Bestellhilfe:** support@your-domain.com

**💡 Tipp:** Bestelle erst 1 Komplett-Set für Prototyping, dann skaliere nach erfolgreichem Test!

---

**🚀 Mit dieser Einkaufsliste hast du alles für ein professionelles Smart Parking System! 🏁**
