# 🔧 WARTUNG & TROUBLESHOOTING - SMART PARKING SYSTEM

## 📅 **WARTUNGSPLAN**

### **🟢 WÖCHENTLICHE INSPEKTION (15 Minuten)**
```bash
⏰ Jeden Montag 09:00 Uhr:
□ Status-LEDs prüfen (grün = OK)
□ App-Dashboard checken (alle Devices online?)
□ Bügel-Bewegung visuell testen (1x hoch/runter)
□ Gehäuse auf Beschädigungen prüfen
□ Sensor-Oberfläche reinigen (trockenes Tuch)

✅ Alles OK? → Nächste Woche
❌ Problem? → Siehe Troubleshooting-Sektion
```

### **🟡 MONATLICHE WARTUNG (1 Stunde)**
```bash
📅 Jeden 1. des Monats:
□ Power-System vollständig prüfen:
  - Akku-Spannung: 12.8-14.4V ✓
  - Solar-Ertrag: >5kWh/Monat ✓
  - MPPT-Controller Status ✓
□ Mechanik-Wartung:
  - Linear Actuator: 3 Tropfen Öl auf Stange
  - Endschalter-Funktion testen
  - Bügel-Befestigung nachziehen
□ Elektronik-Check:
  - Alle Kabelverbindungen fest?
  - Gehäuse-Dichtung intakt?
  - Korrosion an Kontakten?
□ Software-Update:
  - Firmware-Version prüfen
  - Automatische Updates aktiviert?
  - Error-Logs auswerten
□ Performance-Analyse:
  - Occupancy Detection Rate >95%?
  - API Response Times <5s?
  - Signal Strength >-90dBm?
```

### **🔴 JÄHRLICHE GENERALWARTUNG (4 Stunden)**
```bash
📅 Einmal pro Jahr (September):
□ Complete System Overhaul:
  - Akku-Kapazitätstest (Entlade-Test)
  - Solar Panel reinigen + Efficiency-Test
  - Alle Schrauben-Verbindungen prüfen
  - Linear Actuator: Fett erneuern
  - Gehäuse: Dichtungen erneuern
  - SIM-Karte: Datenvolumen prüfen
□ Hardware-Upgrade-Check:
  - Neue Firmware verfügbar?
  - Hardware End-of-Life Status?
  - Performance-Optimierungen?
□ Sicherheits-Audit:
  - Emergency Stop Test
  - Fail-Safe Mechanismen
  - Datenschutz-Compliance
□ Business-Review:
  - ROI-Analyse aktualisieren
  - Wartungskosten bewerten
  - Expansion-Planung
```

---

## 🚨 **TROUBLESHOOTING-MATRIX**

### **❌ SYSTEM KOMPLETT OFFLINE**

#### **Diagnose-Schritte:**
```bash
1. Status-LEDs prüfen:
   Alle aus? → Power-Problem
   Rot blinkend? → Firmware-Crash
   Gelb blinkend? → Netzwerk-Problem

2. Power-System check:
   Multimeter bereitlegen:
   - Akku-Spannung messen (Klemmen 1+2)
   - Solar-Input prüfen (bei Sonne >16V)
   - 5V Rail für ESP32 (4.9-5.1V)
   
3. Visuelle Inspektion:
   - Kabel-Bruch sichtbar?
   - Wasser im Gehäuse?
   - Korrosion an Kontakten?
   - Vandalismus-Schäden?
```

#### **Problem-Lösung Hierarchie:**
```bash
🔋 Power-Problem (80% der Fälle):
   Lösung A: Hauptsicherung prüfen/ersetzen
   Lösung B: Akku-Verbindung nachziehen
   Lösung C: Solar-Panel säubern
   Lösung D: MPPT-Controller Reset
   
📡 Kommunikations-Problem (15% der Fälle):
   Lösung A: SIM-Karte neu einsetzen
   Lösung B: Antennen-Verbindung prüfen
   Lösung C: APN-Einstellungen korrigieren
   Lösung D: Provider-Support kontaktieren
   
🧠 Firmware-Problem (5% der Fälle):
   Lösung A: Hardware-Reset (Button 10s drücken)
   Lösung B: Firmware neu flashen
   Lösung C: Factory Reset durchführen
   Lösung D: Hardware austauschen
```

### **⚡ BÜGEL FUNKTIONIERT NICHT**

#### **Diagnose-Flowchart:**
```bash
🔧 Bügel bewegt sich nicht:
   ├─ Emergency Stop gedrückt?
   │  └─ JA: Emergency Stop entriegeln → Problem gelöst ✅
   │  └─ NEIN: Weiter zu Relay-Test
   ├─ Relay-LEDs leuchten beim Command?
   │  └─ NEIN: ESP32-Problem → GPIO-Pins testen
   │  └─ JA: Weiter zu Motor-Test
   ├─ 12V am Linear Actuator?
   │  └─ NEIN: Relay defekt → Relay-Modul tauschen
   │  └─ JA: Weiter zu Mechanik-Test
   └─ Mechanische Blockade?
      └─ JA: Hindernis entfernen
      └─ NEIN: Linear Actuator defekt → Austausch

🐌 Bügel bewegt sich langsam:
   ├─ Akku-Spannung <12V?
   │  └─ JA: Akku laden/ersetzen
   ├─ Linear Actuator verschmutzt?
   │  └─ JA: Reinigen + Ölen
   └─ Mechanische Reibung?
      └─ JA: Lager schmieren

🔄 Bügel stoppt nicht an Endposition:
   ├─ Endschalter-LEDs funktional?
   │  └─ NEIN: Endschalter justieren/ersetzen
   ├─ Kabel-Verbindung OK?
   │  └─ NEIN: Kabel reparieren
   └─ Software-Bug?
      └─ JA: Firmware-Update
```

### **📊 SENSOR ZEIGT FALSCHE WERTE**

#### **Ultraschall-Sensor Probleme:**
```bash
🎯 Occupancy Detection fehlerhaft:

Problem: "Auto da, aber Sensor zeigt FREI"
   Diagnose: Ultraschall-Echo zu schwach
   Ursachen:
   - Verschmutzung der Sensor-Oberfläche
   - Winkel zum Auto ungünstig (>45°)
   - Auto-Material reflektiert schlecht (Matt-Schwarz)
   - Interferenz durch andere Ultraschall-Quellen
   
   Lösungen:
   ✅ Sensor mit Druckluft reinigen
   ✅ Sensor-Position um 15° anpassen  
   ✅ Schwellwert von 200cm auf 250cm erhöhen
   ✅ Messintervall von 5s auf 2s reduzieren
   ✅ Multi-Sample-Averaging aktivieren (3 Messungen)

Problem: "Kein Auto, aber Sensor zeigt BESETZT"
   Diagnose: False-Positive Detection
   Ursachen:
   - Vögel/Tiere im Messbereich
   - Staub/Schnee auf Sensor
   - Reflektionen von nahestehenden Objekten
   - Temperatur-bedingte Drift
   
   Lösungen:
   ✅ PIR-Sensor als Plausibilitäts-Check aktivieren
   ✅ Mindest-Detection-Zeit auf 30s erhöhen
   ✅ Sensor-Hood gegen Seitenlicht installieren
   ✅ Temperature-Compensation aktivieren
   ✅ Machine Learning Filter implementieren

Problem: "Sensor-Werte schwanken stark"
   Diagnose: Elektronische Interferenz
   Ursachen:
   - 4G-Modul sendet während Messung
   - Relay-Schalten erzeugt EMV
   - Power-Supply-Ripple
   - Defekte Verkabelung
   
   Lösungen:
   ✅ Sensor-Messung zwischen 4G-Transmissions
   ✅ Ferrit-Filter an Sensor-Kabeln
   ✅ Separate 5V-Regulation für Sensor
   ✅ Geschirmte Kabel verwenden
   ✅ Software-Filter: Median über 5 Samples
```

### **🔋 POWER-SYSTEM PROBLEME**

#### **Akku lädt nicht:**
```bash
🔍 Diagnose-Schritte:
1. Solar-Panel Spannung bei Sonne messen:
   Erwartet: 18-22V
   <16V: Panel defekt/verschmutzt/verschattet
   >25V: Leerlauf, keine Last-Verbindung

2. MPPT-Controller Status-LEDs:
   Grün blinkend: Normal charging
   Rot blinkend: Überspannung/Kurzschluss
   Aus: Kein Solar-Input oder defekt

3. Akku-Spannung unter Last:
   >13V: Akku OK
   12-13V: Akku schwach, laden erforderlich
   <12V: Akku tiefentladen, ggf. defekt

🔧 Lösungsansätze:
□ Solar Panel mit Wasser + Schwamm reinigen
□ Verschattung entfernen (Blätter, Schnee)
□ MC4-Stecker auf Korrosion prüfen
□ MPPT-Controller Reset: 5min stromlos
□ Akku-Pole reinigen + nachfetten
□ Load-Disconnect testen: App → "Sleep Mode"
□ Bei Akku-Defekt: Warnung an Maintenance-Team
```

#### **System läuft nicht durch die Nacht:**
```bash
⚡ Power-Budget-Analyse:
Stromverbrauch pro 24h:
- ESP32-S3: 120mA × 24h = 2.88Ah
- SIM7600E Standby: 25mA × 24h = 0.6Ah  
- SIM7600E Active: 500mA × 1h = 0.5Ah
- Linear Actuator: 2A × 0.1h = 0.2Ah
- Sensoren: 30mA × 24h = 0.72Ah
Total: ~4.9Ah/Tag

Akku-Kapazität: 20Ah
Erwartete Laufzeit: 20Ah ÷ 4.9Ah = 4.1 Tage

Wenn kürzer:
□ Stromverbrauch messen (Clamp-Meter)
□ Sleep-Mode Effizienz prüfen
□ Akku-Kapazität testen (Load-Test)
□ Power-Management optimieren:
  - 4G Intervall verlängern: 60s → 300s
  - ESP32 Deep-Sleep zwischen Messungen
  - Sensor Power-Down wenn nicht aktiv
```

### **📡 KOMMUNIKATIONS-PROBLEME**

#### **Keine Verbindung zum Backend:**
```bash
🌐 Netzwerk-Diagnose:
1. AT-Command-Test mit Terminal:
   AT+CREG?    → 0,1 = Registered
   AT+CGATT?   → 1 = GPRS attached
   AT+CIFSR    → IP-Adresse anzeigen
   AT+CSQ      → Signal: >15 gut, <10 schlecht

2. HTTP-Test manuell:
   AT+HTTPINIT
   AT+HTTPPARA="CID",1
   AT+HTTPPARA="URL","https://httpbin.org/get"
   AT+HTTPACTION=0
   AT+HTTPREAD  → Response anzeigen

3. Backend-Erreichbarkeit:
   Von anderem Gerät testen:
   curl -X POST https://your-domain.com/api/hardware/register
   Response 200 OK? → Backend funktional
   Timeout? → Server/Domain Problem

🔧 Häufige Lösungen:
□ SIM-Karte in Smartphone testen (Datenvolumen?)
□ APN-Settings korrigieren (Provider abhängig)
□ Antennen-Verbindung festziehen
□ Standort mit besserer Coverage wählen
□ Backend-URL in Firmware prüfen (https!)
□ Firewall/VPN-Probleme ausschließen
```

#### **Verbindung bricht ab:**
```bash
📶 Instabile Verbindung:
Symptome:
- Device registriert sich, dann offline
- Heartbeat unregelmäßig
- Commands kommen nicht an

Root-Cause-Analyse:
1. Signal-Strength-Log auswerten:
   CSQ-Werte über Zeit plotten
   Schwankungen >±5 = Coverage-Problem
   
2. Power-Management-Conflict:
   4G-Modul braucht 500-2000mA peak
   Bei schwachem Akku: Voltage-Drop
   → Modul reset sich selbst
   
3. Provider-Throttling:
   Übermäßiger Datenverbrauch?
   Fair-Use-Policy erreicht?
   Account-Status prüfen

🛠️ Optimierungen:
□ Adaptive Heartbeat: Schlechtes Signal = längere Intervalle
□ Power-Boost für 4G: Kondensator-Puffer
□ Daten-Kompression: JSON → MessagePack
□ Retry-Logic: Exponential Backoff
□ Fallback-APN konfigurieren
```

---

## 🔧 **ERSATZTEIL-MANAGEMENT**

### **📦 KRITISCHE ERSATZTEILE (Immer vorrätig)**
```bash
🚨 Tier 1 - Mission Critical (24h Verfügbarkeit):
□ ESP32-S3 Development Board (2 Stück)
   Part-No: ESP32-S3-DevKitC-1
   Lieferant: Espressif/DigiKey
   Kosten: 25€/Stück
   
□ SIM7600E 4G Module (1 Stück)
   Part-No: SIM7600E-H
   Lieferant: Waveshare
   Kosten: 89€/Stück
   
□ Linear Actuator 12V 50mm (1 Stück)
   Part-No: PA-14P-6-50
   Lieferant: Progressive Automations  
   Kosten: 180€/Stück

□ LiFePO4 Akku 12V 20Ah (1 Stück)
   Part-No: LiTime 12V20Ah
   Lieferant: LiTime/Amazon
   Kosten: 159€/Stück

⚡ Tier 2 - Wichtige Komponenten (1 Woche):
□ MPPT Solar Controller (1 Stück)
□ Ultraschall Sensor JSN-SR04T (2 Stück)
□ Relay Module 2-Channel (2 Stück)  
□ DC-DC Converter 12V→5V (2 Stück)
□ Micro-Endschalter (4 Stück)
□ Antennen GSM/GPS (1 Set)

🔩 Tier 3 - Verbrauchsmaterial:
□ Sicherungen 20A (10 Stück)
□ PG7 Kabelverschraubungen (10 Stück)
□ M8 Edelstahl-Schrauben (20 Stück)
□ Kupfer-Kabelschuhe (20 Stück)
□ Isolierband + Schrumpfschlauch
□ Kontaktspray + Korrosionsschutz
```

### **🔄 AUSTAUSCH-PROZEDUREN**

#### **ESP32 Module Replacement:**
```bash
⚠️ Vor Austausch:
1. Backup erstellen:
   - Flash-Inhalt über esptool.py auslesen
   - Device-ID und Konfiguration notieren
   - Letzte bekannte Firmware-Version

🔧 Austausch-Schritte:
1. Power komplett abschalten (Hauptsicherung)
2. Altes ESP32 dokumentiert abklemmen:
   - Foto von Verkabelung machen
   - Pin-Belegung auf Zettel notieren
3. Neues ESP32 identisch verkabeln
4. Firmware flashen:
   - Aktuelle Version von GitHub
   - Device-ID konfigurieren
   - Kalibrierungs-Parameter übertragen
5. Funktionstest:
   - Serial Monitor für Boot-Log
   - Sensor-Readings plausibel?
   - 4G-Connection OK?
   - Actuator-Commands funktional?
6. Registration im Backend:
   - Falls neue Hardware-ID: Re-Registration
   - Device-Status auf "ACTIVE" setzen
   - Monitoring für 24h intensivieren

⏱️ Geschätzte Dauer: 45 Minuten
🔧 Benötigtes Werkzeug: Laptop + USB-Kabel
```

#### **Linear Actuator Replacement:**
```bash
⚠️ Sicherheits-Hinweise:
- Bügel vor Austausch in sichere Position (UP)
- Mechanische Sicherung einbauen (Klemmkeil)
- 12V Power abschalten (Relay-Sicherung)

🔧 Demontage:
1. Bügel in UP-Position fahren
2. Mechanischen Stopper einbauen
3. Elektrische Verbindungen lösen + kennzeichnen
4. Kugelgelenk-Verbindung lösen
5. Basis-Befestigung abschrauben
6. Alten Actuator entfernen

🔧 Montage:
1. Neuen Actuator in exakt gleicher Position
2. Basis-Schrauben mit Drehmoment 25Nm
3. Kugelgelenk-Verbindung korrekt ausrichten
4. Elektrische Verbindung nach Farbcode
5. Mechanischen Stopper entfernen
6. Funktionstest ohne Last:
   - Manual UP/DOWN Commands
   - Endschalter-Auslösung prüfen
   - Smooth Movement überprüfen
7. Full-Load-Test mit Bügel
8. Emergency Stop Test

⏱️ Geschätzte Dauer: 90 Minuten
🔧 Benötigtes Werkzeug: Schraubenschlüssel, Multimeter
```

---

## 📊 **MONITORING & ALERTING**

### **🔔 Automatische Benachrichtigungen**
```bash
🚨 Critical Alerts (Sofortige SMS):
- Device Offline >15 Minuten
- Akku-Spannung <11.5V (Tiefentladung)
- Emergency Stop aktiviert
- Mechanischer Fehler (Endschalter)
- API-Errors >5 in 10 Minuten

⚠️ Warning Alerts (E-Mail):
- Signal Strength <-90dBm
- Akku-Kapazität <30%
- Solar-Ertrag <Soll-Wert (wetterabhängig)
- Response Times >10s
- Sensor-Genauigkeit <90%

ℹ️ Info Alerts (Dashboard):
- Wartung fällig (basiert auf Betriebsstunden)
- Firmware-Update verfügbar
- Performance-Trends
- Usage-Statistiken
- Cost-per-Transaction Updates
```

### **📈 Performance-KPIs Dashboard**

#### **Real-Time Metriken:**
```bash
🟢 System Health (grün >95%, gelb 90-95%, rot <90%):
- Uptime Percentage: 99.7% ✅
- Occupancy Detection Accuracy: 97.3% ✅  
- Barrier Response Time: 6.2s ✅
- API Success Rate: 99.1% ✅
- Power System Efficiency: 94.8% ✅

📊 Daily Statistics:
- Parking Sessions: 47
- Revenue Generated: CHF 127.50
- Energy Consumed: 4.2Ah
- Solar Energy Harvested: 6.8Ah
- 4G Data Usage: 125MB
- Barrier Cycles: 94 (47×2)

📈 Weekly Trends:
- Session Growth: +12% vs. last week
- Revenue Growth: +18% vs. last week  
- System Reliability: 99.4% average
- Maintenance Incidents: 0
- Customer Satisfaction: 4.8/5
```

### **🔍 Predictive Maintenance**

#### **Machine Learning Alerting:**
```bash
🤖 AI-Powered Predictions:
- Akku EOL Prediction: 18 Monate (basiert auf Kapazitäts-Trend)
- Linear Actuator Wear: 89.000 Zyklen verbleibend
- Solar Panel Degradation: 0.3%/Jahr (normal)
- 4G Module MTBF: >5 Jahre (temperaturabhängig)

📉 Anomaly Detection:
- Ungewöhnliche Stromverbrauch-Patterns
- Sensor-Drift über Zeit
- Kommunikations-Latenzen außerhalb Normal-Band
- Mechanische Vibrationen (durch Accelerometer)

⚡ Maintenance Triggers:
- Automatisch: Wenn Prediction <30 Tage
- Manuell: Admin kann Wartung forcieren
- Scheduled: Basiert auf Betriebsstunden
- Emergency: Bei kritischen System-Fehlern
```

---

## 🎯 **SUPPORT-ESKALATION**

### **📞 Support-Levels:**

#### **🥇 Level 1 - Self-Service (Betreiber)**
```bash
Typische Probleme:
- Device temporär offline
- Bügel reagiert langsam
- Sensor zeigt sporadisch falsche Werte
- Akku-Warnung

Tools:
- Diese Troubleshooting-Anleitung
- Admin-Dashboard mit Diagnostics
- Remote-Reboot über App
- Basic-Tests ohne Werkzeug

Eskalation wenn:
- Problem nicht in 30min gelöst
- Hardware-Defekt vermutet
- Sicherheits-relevante Probleme
```

#### **🥈 Level 2 - Remote-Support (Tech-Team)**
```bash
Zuständigkeit:
- Firmware-Updates Remote
- Backend-Konfiguration
- Erweiterte Diagnostics
- Parameter-Optimierung

Tools:
- SSH-Zugang zu Backend
- Firmware-OTA-Updates
- Telemetrie-Datenbank
- Remote-Debugging

Verfügbarkeit:
- Mo-Fr 8:00-18:00
- Wochenende: Emergency Only
- Response Time: <4h
```

#### **🥉 Level 3 - Vor-Ort-Service (Hardware-Techniker)**
```bash
Zuständigkeit:
- Hardware-Reparatur/-Austausch
- Mechanische Justierung
- Verkabelungs-Probleme
- Installation neuer Komponenten

Ausrüstung:
- Vollständiger Ersatzteil-Satz
- Professionelles Werkzeug
- Messgeräte (Multimeter, Oszilloskop)
- Laptop mit Entwicklungsumgebung

Verfügbarkeit:
- Mo-Fr 7:00-19:00
- Notdienst: +49-XXX-EMERGENCY
- Response Time: <24h
```

### **📋 Eskalations-Matrix:**

| Problem | Severity | Level | Response Time | Lösung erwartet |
|---------|----------|-------|---------------|-----------------|
| Device Offline | High | L1→L2 | 15min→2h | Remote-Reboot |
| Actuator defekt | High | L1→L3 | 30min→24h | Hardware-Austausch |
| Sensor ungenau | Medium | L1→L2 | 1h→8h | Parameter-Tuning |
| Akku schwach | Medium | L1→L3 | 2h→48h | Akku-Service |
| Kommunikation instabil | Low | L1→L2 | 4h→24h | Config-Optimierung |
| Gehäuse beschädigt | Low | L3 | 24h→1 Woche | Reparatur/Ersatz |

---

## 💡 **OPTIMIERUNGS-TIPPS**

### **⚡ Performance-Optimierung:**
```bash
🚀 Sensor-Accuracy Tuning:
- Multi-Sample-Averaging: 3→5 Samples
- Temperature-Compensation aktivieren
- PIR-Motion als Plausibilitäts-Check
- Machine-Learning Filter trainieren

🔋 Power-Efficiency:
- Deep-Sleep zwischen Measurements (ESP32)
- 4G-Module Power-Down bei stabiler Connection
- Adaptive Heartbeat-Frequenz
- Solar-Panel optimal ausrichten (süd, 30°)

📡 Communication-Reliability:
- Dual-SIM Setup für Redundanz
- Mesh-Networking zwischen nahestehenden Devices
- LoRaWAN als Backup-Channel
- Edge-Computing für kritische Entscheidungen

🔧 Mechanical-Longevity:
- Linear Actuator: Regelmäßige Schmierung
- Endschalter: Kontakt-Spray gegen Korrosion
- Bügel-Material: Edelstahl statt Aluminium
- Vibration-Dampening für elektronische Komponenten
```

### **💰 Cost-Optimization:**
```bash
📊 Operational-Cost-Reduction:
- Bulk-SIM-Verträge aushandeln (>10 Devices)
- Predictive Maintenance statt reaktiv
- Energy-Harvesting-Efficiency maximieren
- Remote-Monitoring reduziert Vor-Ort-Besuche

🔄 Lifecycle-Management:
- Component-Refresh alle 3-5 Jahre planen
- Firmware-LTS-Versionen für Stabilität
- Hardware-Standardisierung für Skalierungseffekte
- Refurbishment-Program für defekte Komponenten
```

---

**🎯 Mit diesem Wartungshandbuch betreibst du dein Smart Parking System professionell und kosteneffizient! 🚀**

**💡 Proaktive Wartung verhindert 80% aller Ausfälle - Checklisten konsequent befolgen! ✅**
