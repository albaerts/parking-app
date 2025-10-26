# 🔧 SMART PARKING HARDWARE - SCHRITT-FÜR-SCHRITT INSTALLATION

## 🎯 **INSTALLATIONSPLAN (3 TAGE)**

### **📅 TAG 1: FUNDAMENT & MECHANIK (8 Stunden)**
### **📅 TAG 2: ELEKTRONIK & POWER (8 Stunden)**  
### **📅 TAG 3: SOFTWARE & TESTS (8 Stunden)**

---

## 📅 **TAG 1: FUNDAMENT & MECHANISCHE INSTALLATION**

### **🌅 08:00 - VORBEREITUNG**
#### **Werkzeug bereitstellen:**
- [ ] Akkuschrauber + Bits
- [ ] Steinbohrer 8mm (SDS-Plus)
- [ ] Schlagbohrmaschine
- [ ] Wasserwaage
- [ ] Maßband/Zollstock
- [ ] Anreißnadel + Hammer
- [ ] Chemie-Anker Set
- [ ] Schraubenschlüssel Set

#### **Material prüfen:**
- [ ] Linear Actuator komplett
- [ ] Metall-Bügel
- [ ] M8 Dübel + Schrauben (4 Sets)
- [ ] Basis-Platte (20x20cm)
- [ ] Chemie-Anker Kartuschen

### **📏 08:30 - VERMESSUNG & MARKIERUNG**
```bash
1. Parkplatz-Ende lokalisieren (optimal: 60cm vom Ende)
2. Bügel-Position markieren (mittig, senkrecht zur Fahrtrichtung)
3. 4 Bohrpunkte anzeichnen (Basis-Platte als Schablone)
4. Abstand zu Hindernissen prüfen (min. 50cm)
5. Höhen-Niveau überprüfen (Gefälle <5%)
```

### **🔨 09:00 - BOHRARBEITEN**
```bash
# Bohrlöcher erstellen:
1. Steinbohrer 8mm einspannen
2. 4 Löcher bohren: 15cm tief, senkrecht
3. Bohrlöcher reinigen (Druckluft/Bürste)
4. Tiefe mit Stahlstab kontrollieren
5. Risse im Beton prüfen
```

**⚠️ SICHERHEIT:**
- Schutzbrille + Gehörschutz tragen
- Staubmaske bei Bohrarbeiten
- Stromleitungen vorher orten!

### **🔗 09:30 - VERANKERUNG**
```bash
# Chemie-Anker setzen:
1. Kartuschen-Spitze abschneiden
2. Mischrohr aufstecken  
3. Chemie in Bohrloch einspritzen (2/3 voll)
4. M8 Dübel langsam eindrehen
5. 2 Stunden aushärten lassen! ⏰
```

### **☕ 10:30 - PAUSE (Aushärtezeit nutzen)**
```bash
# Während Wartezeit:
- Kaffee trinken ☕
- Material für Tag 2 sortieren
- Elektronik-Komponenten prüfen
- Wetter für Tag 2 checken
```

### **🔧 12:30 - BASIS-PLATTE MONTAGE**
```bash
1. Basis-Platte ausrichten (Wasserwaage!)
2. M8 Schrauben durch Platte in Dübel
3. Kreuzweise anziehen (gleichmäßig)
4. Drehmoment: 25 Nm (handfest + 1/4 Umdrehung)
5. Stabilität testen (kein Wackeln!)
```

### **⚡ 13:00 - LINEAR ACTUATOR MONTAGE**
```bash
# Actuator befestigen:
1. Actuator auf Basis-Platte positionieren
2. Befestigungs-Schrauben eindrehen
3. Bewegungsrichtung prüfen (frei schwenkbar?)
4. Kabel-Ausführung markieren (zum Gehäuse)
5. Provisorische Kabel-Zugentlastung
```

### **🏗️ 14:00 - BÜGEL-MECHANISMUS**
```bash
# Bügel montieren:
1. Bügel an Actuator-Stange befestigen
2. Kugelgelenk richtig ausrichten
3. Schwenk-Bereich testen (360° frei?)
4. Endpositionen definieren:
   - UP: Vertikal (90°)
   - DOWN: Horizontal über Boden (5cm)
5. Bewegung manuell testen
```

### **🔧 15:00 - ENDSCHALTER INSTALLATION**
```bash
# Limit Switches montieren:
1. UP-Schalter an Basis montieren
2. DOWN-Schalter positionieren  
3. Mechanische Auslösung testen
4. Kabel wasserdicht verlegen
5. Vorläufige Verkabelung zum Gehäuse
```

### **✅ 15:30 - MECHANIK-TESTS**
```bash
# Funktions-Tests:
1. Manueller Bügel-Test (smooth movement?)
2. Endschalter-Auslösung prüfen
3. Keine mechanischen Blockaden?
4. Kabel-Zugentlastung OK?
5. Foto dokumentieren für Tag 2
```

### **📋 16:00 - TAG 1 ABSCHLUSS**
- [ ] Mechanik komplett installiert
- [ ] Endschalter funktional
- [ ] Kabel provisorisch gelegt
- [ ] Werkzeug für Tag 2 vorbereitet
- [ ] Material-Check für Elektronik

---

## 📅 **TAG 2: ELEKTRONIK & POWER-SYSTEM**

### **🌅 08:00 - GEHÄUSE INSTALLATION**
#### **Standort-Wahl:**
- 2m Abstand vom Bügel (Kabel-Reichweite)
- 1.5m Höhe (Vandalismus-Schutz)
- Süd-Ausrichtung für Solar Panel
- Freie Sicht für GSM-Antenne

#### **Montage:**
```bash
1. Wandhalterung/Mast installieren
2. Gehäuse ausrichten (Wartungs-Zugang)
3. Solar Panel auf Deckel montieren (30° Neigung)
4. PG7 Kabeldurchführungen einbauen
5. Erdungs-Anschluss (Blitzschutz)
```

### **☀️ 09:00 - SOLAR-SYSTEM**
```bash
# Solar Panel anschließen:
1. MC4-Stecker wasserdicht verbinden
2. Kabel durch PG7 ins Gehäuse
3. Polarität prüfen! (Rot=+, Schwarz=-)
4. Erste Spannungsmessung (Multimeter)
   - Sonne: 18-22V
   - Schatten: <5V
```

### **🔋 10:00 - POWER-VERKABELUNG**
```bash
# MPPT Controller Installation:
1. Controller im Gehäuse befestigen
2. Solar+ → MPPT Solar+
3. Solar- → MPPT Solar-
4. Akku+ → 20A Sicherung → MPPT Batt+
5. Akku- → MPPT Batt-

# DC-DC Converter:
6. MPPT Load+ → DC-DC Input+
7. MPPT Load- → DC-DC Input-
8. DC-DC Output: 5V → ESP32 VIN
```

**⚠️ SICHERHEIT:**
- Immer + vor - anschließen
- Kurzschluss vermeiden!
- Sicherung als letztes einbauen

### **📊 11:00 - SENSOR-VERKABELUNG**
```bash
# Ultraschall JSN-SR04T:
VCC → 5V Rail
GND → Common GND
Trig → ESP32 Pin 2  
Echo → ESP32 Pin 3

# Endschalter:
Limit UP → ESP32 Pin 4 + GND
Limit DOWN → ESP32 Pin 5 + GND

# PIR Motion:
VCC → 3.3V Rail
OUT → ESP32 Pin 6
GND → Common GND
```

### **☕ 12:00 - MITTAGSPAUSE**

### **🧠 13:00 - ESP32 + SIM-MODUL**
```bash
# ESP32-S3 Installation:
1. ESP32 auf Breadboard/PCB montieren
2. Power-Versorgung anschließen (5V → VIN)
3. GPIO-Verkabelung nach Plan
4. Status-LED anschließen (Pin 9)

# SIM7600E Modul:
5. SIM-Karte einlegen (richtige Orientierung!)
6. Antennen anschließen (GSM + GPS)
7. UART-Verbindung: TX→Pin17, RX→Pin18
8. Power Control → Pin 19
```

### **⚡ 14:00 - ACTUATOR-STEUERUNG**
```bash
# Relay-Modul verkabeln:
ESP32 Pin 7 → Relay1 IN (UP)
ESP32 Pin 8 → Relay2 IN (DOWN)
12V Akku+ → Relay COM (beide)
Relay1 NO → Actuator +
Relay2 NO → Actuator -
Actuator GND → Akku GND

# Emergency Stop:
Emergency Button → ESP32 Pin 10 + GND
(Öffner-Kontakt, Pull-up intern)
```

### **🔌 15:00 - SPANNUNGS-TESTS**
```bash
# Power-System prüfen:
1. Akku-Spannung: 12-14.4V ✓
2. Solar-Ladung: MPPT LEDs ✓
3. 5V Rail: 4.9-5.1V ✓
4. 3.3V ESP32: 3.2-3.4V ✓
5. Alle GND verbunden ✓

# Sensor-Spannungen:
- Ultraschall: 5V ✓
- Endschalter: 3.3V Pull-up ✓
- PIR: 3.3V ✓
```

### **🔧 16:00 - ERSTE POWER-ON TESTS**
```bash
# System hochfahren:
1. Haupt-Sicherung einsetzen
2. ESP32 sollte starten (Status-LED?)
3. SIM-Modul Power-LED prüfen
4. MPPT Display: Akku-Ladung
5. Keine Rauchentwicklung! 🚨
```

### **📋 16:30 - TAG 2 ABSCHLUSS**
- [ ] Power-System funktional
- [ ] Alle Spannungen korrekt
- [ ] Sensoren verkabelt
- [ ] Actuator-Steuerung bereit
- [ ] Gehäuse wetterdicht verschlossen

---

## 📅 **TAG 3: SOFTWARE & INBETRIEBNAHME**

### **🌅 08:00 - FIRMWARE VORBEREITUNG**
#### **Arduino IDE Setup:**
```bash
1. Arduino IDE öffnen
2. ESP32 Board Package installiert? ✓
3. Libraries installieren:
   - ArduinoJson
   - SoftwareSerial
   - WiFi (ESP32 Core)
4. COM-Port identifizieren
```

#### **Code-Anpassung:**
```cpp
// smart_parking_firmware.ino anpassen:
const char* DEVICE_ID = "PARK_DEVICE_001";  // Eindeutig!
const char* API_BASE = "https://deine-domain.com/api";
const char* APN = "internet";  // Provider-spezifisch

// Spot-ID konfigurieren:
doc["spot_id"] = "SPOT_001";  // In registerDevice()
```

### **📱 09:00 - FIRMWARE UPLOAD**
```bash
# ESP32 programmieren:
1. USB-Kabel an ESP32 anschließen
2. Board: "ESP32S3 Dev Module"
3. Port: COM-Port auswählen
4. Upload Speed: 921600
5. Compile & Upload ⬆️
6. Serial Monitor öffnen (115200 baud)
```

### **📡 10:00 - SIM-VERBINDUNG TESTEN**
```bash
# SIM-Modul Diagnose:
1. AT Commands prüfen:
   AT          → OK
   AT+CPIN?    → READY
   AT+CREG?    → 0,1 (registered)
   AT+CSQ      → Signal Strength (>15 gut)

2. Netzwerk-Registration:
   - LED-Status am SIM-Modul?
   - Provider im Display?
   - IP-Adresse erhalten?
```

### **🌐 11:00 - API-VERBINDUNG**
```bash
# Backend-Kommunikation:
1. Device Registration testen
2. HTTP POST an /hardware/register
3. Response: 200 OK?
4. Device in Backend-Database sichtbar?
5. Heartbeat-Interval starten
```

### **☕ 12:00 - MITTAGSPAUSE**

### **📊 13:00 - SENSOR-KALIBRIERUNG**
```bash
# Ultraschall-Sensor:
1. Freier Parkplatz: >300cm oder Timeout
2. Auto anwesend: 15-200cm
3. Schwellwerte in Code anpassen:
   
bool isOccupied(float distance) {
  return (distance >= 15 && distance <= 200);
}

# Test mit echtem Auto:
- Auto hinfahren → "OCCUPIED" im Log? ✓
- Auto wegfahren → "FREE" im Log? ✓
```

### **⚡ 14:00 - BÜGEL-STEUERUNG TESTEN**
```bash
# Actuator-Tests:
1. Manual Command: "raise_barrier"
   - Relay 1 aktiviert? ✓
   - Bügel fährt hoch? ✓
   - Endschalter UP löst aus? ✓
   - Motor stoppt? ✓

2. Manual Command: "lower_barrier"
   - Relay 2 aktiviert? ✓
   - Bügel fährt runter? ✓
   - Endschalter DOWN löst aus? ✓
   - Motor stoppt? ✓

3. Emergency Stop Test:
   - Button drücken während Bewegung
   - Sofortiger Stopp? ✓
   - LED blinkt? ✓
```

### **🎛️ 15:00 - SYSTEM-INTEGRATION**
```bash
# App-Steuerung testen:
1. Owner-Login in App
2. Hardware-Tab aufrufen
3. Device Status sichtbar? ✓
4. Bügel-Befehle senden:
   - "Hoch" Button → Bügel hoch ✓
   - "Runter" Button → Bügel runter ✓
5. Echtzeit-Updates im Dashboard ✓
```

### **🔄 16:00 - LIVE-TEST MIT AUTO**
```bash
# Vollständiger Workflow:
1. Auto nähert sich → App zeigt "FREI"
2. User bucht Parkplatz → Bügel fährt automatisch hoch
3. Auto parkt ein → Sensor erkennt "BESETZT"
4. Bügel fährt automatisch runter (Sicherheit)
5. Auto fährt weg → Sensor erkennt "FREI"
6. Session wird beendet → Einnahmen gebucht ✓
```

### **📊 17:00 - MONITORING & FINE-TUNING**
```bash
# Power-Management:
- Battery Level: >80% ✓
- Solar Charging: Aktiv bei Sonne ✓
- Stromverbrauch: <100mA Standby ✓

# Kommunikation:
- Heartbeat alle 30s ✓
- Signal Strength: >-90dBm ✓
- API Response Times: <5s ✓

# Mechanik:
- Smooth Movement ✓
- Keine Geräusche ✓
- Endschalter präzise ✓
```

### **📋 17:30 - ABNAHME & DOKUMENTATION**
- [ ] Vollständiger Funktionstest bestanden
- [ ] Sicherheitstest (Emergency Stop) OK
- [ ] Power-System autark funktional
- [ ] App-Integration vollständig
- [ ] Installationsprotokoll erstellt
- [ ] Wartungsplan übergeben
- [ ] Endkunde-Schulung durchgeführt

---

## 🔍 **QUALITÄTSKONTROLLE - CHECKLISTE**

### **🔧 Mechanik:**
- [ ] Bügel-Bewegung smooth (kein Ruckeln)
- [ ] Endschalter lösen zuverlässig aus
- [ ] Kein mechanisches Spiel
- [ ] Emergency Stop funktional
- [ ] Befestigung rock-solid

### **⚡ Elektronik:**
- [ ] Alle Spannungen im Toleranzbereich
- [ ] Keine losen Verbindungen
- [ ] Gehäuse wasserdicht
- [ ] Kabel-Zugentlastung OK
- [ ] Sicherungen richtig dimensioniert

### **📡 Kommunikation:**
- [ ] SIM-Karte registriert
- [ ] API-Verbindung stabil
- [ ] Heartbeat-Intervall konstant
- [ ] Commands werden ausgeführt
- [ ] Datenschutz gewährleistet

### **🔋 Power:**
- [ ] Solar-Ladung funktional
- [ ] Akku-Kapazität ausreichend
- [ ] Tiefentladeschutz aktiv
- [ ] Power-Management optimiert
- [ ] Backup-Strategie definiert

### **📊 Software:**
- [ ] Sensor-Kalibrierung korrekt
- [ ] Occupancy Detection zuverlässig
- [ ] App-Integration vollständig
- [ ] Error Handling implementiert
- [ ] Logging & Monitoring aktiv

---

## 🚨 **TROUBLESHOOTING-GUIDE**

### **❌ Problem: ESP32 startet nicht**
```bash
Diagnose:
1. Power LED am ESP32? Nein → Power-Problem
2. Serial Output? Nein → Firmware-Problem
3. Boot-Loop? → Memory/Code-Problem

Lösung:
- 5V Spannung messen (4.9-5.1V)
- USB-Kabel tauschen
- Firmware neu flashen
- Factory Reset durchführen
```

### **❌ Problem: Keine SIM-Verbindung**
```bash
Diagnose:
1. AT Commands → Timeout? → SIM-Modul defekt
2. CPIN? → SIM ERROR → SIM-Karte Problem
3. CREG? → Not registered → Netz-Problem

Lösung:
- SIM-Karte in Handy testen
- Antennen-Verbindung prüfen
- APN konfigurieren
- Provider kontaktieren
```

### **❌ Problem: Bügel bewegt sich nicht**
```bash
Diagnose:
1. 12V am Actuator messen
2. Relay-LEDs leuchten?
3. Emergency Stop gedrückt?
4. Endschalter blockiert?

Lösung:
- Sicherung prüfen
- Relay-Modul tauschen
- Emergency Stop entriegeln
- Endschalter justieren
```

### **❌ Problem: Sensor zeigt falsche Werte**
```bash
Diagnose:
1. Ultraschall Echo empfangen?
2. Verkabelung korrekt?
3. Interferenzen (andere Sensoren)?
4. Verschmutzung/Beschädigung?

Lösung:
- Sensor reinigen
- Kabel-Kontinuität prüfen
- Position/Winkel anpassen
- Schwellwerte kalibrieren
```

### **❌ Problem: Akku lädt nicht**
```bash
Diagnose:
1. Solar-Spannung bei Sonne? <16V → Panel Problem
2. MPPT-LEDs? Aus → Controller Problem
3. Akku-Spannung steigt nicht? → Akku defekt

Lösung:
- Panel-Verkabelung prüfen
- Verschattung entfernen
- MPPT-Controller Reset
- Akku-Kapazität messen
```

---

## 📞 **SUPPORT-KONTAKTE**

### **🔧 Hardware-Support:**
- **ESP32 Probleme:** community.platformio.org
- **SIM-Modul:** Waveshare Support
- **Linear Actuator:** Progressive Automations

### **📱 Software-Support:**
- **Arduino IDE:** arduino.cc/en/support
- **API-Integration:** Projekt-Dokumentation
- **Firmware-Updates:** GitHub Repository

### **⚡ Power-System:**
- **Solar-Komponenten:** Offgridtec Support
- **MPPT-Controller:** Victron Community
- **LiFePO4-Akku:** LiTime Support

### **🚨 Notfall-Kontakte:**
- **Elektriker:** [Lokaler Kontakt]
- **Metallbauer:** [Lokaler Kontakt]
- **IT-Support:** [Projekt-Team]

---

## 🎯 **ERFOLGS-KRITERIEN**

### **✅ Installation erfolgreich wenn:**
- Vollautomatischer Betrieb 24/7
- Sensor-Erkennung >95% Genauigkeit
- Bügel-Steuerung <10s Response-Zeit
- Power-System >7 Tage autark
- App-Integration Real-Time Updates
- Wartungsintervall >1 Monat

### **🏆 System-Performance:**
- **Verfügbarkeit:** >99.5% Uptime
- **Batterie-Laufzeit:** >168h ohne Sonne
- **Kommunikation:** <5s API Response
- **Mechanik:** >100.000 Zyklen MTBF
- **Vandalismus-Resistenz:** IP65 + Sicherung

---

**🚀 Mit dieser Anleitung installierst du ein professionelles Smart Parking System! 🎯**

**💡 Bei Problemen: Schritt-für-Schritt Troubleshooting befolgen und Support kontaktieren.**
