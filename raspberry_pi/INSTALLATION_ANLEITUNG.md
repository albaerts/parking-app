# 🍓 RASPBERRY PI PARKBÜGEL - INSTALLATIONSANLEITUNG

## 📋 **SCHRITT-FÜR-SCHRITT SETUP**

### **1️⃣ HARDWARE VERKABELN (15 Minuten)**

#### **🔌 GPIO-VERBINDUNGEN:**
```bash
BREADBOARD SETUP:
┌─────────────────────────────────┐
│  Pi GPIO → Breadboard → Bauteil │
├─────────────────────────────────┤
│  📍 SERVO SG90:                 │
│  • Pin 2 (5V)    → Rot (VCC)   │
│  • Pin 6 (GND)   → Braun (GND) │  
│  • Pin 12(GPIO18)→ Orange (PWM) │
│                                 │
│  💡 STATUS LEDs:                │
│  • Pin 16(GPIO23)→ Grüne LED    │
│  • Pin 18(GPIO24)→ Rote LED     │
│  • Pin 22(GPIO25)→ Blaue LED    │
│  • Alle LEDs → 220Ω → GND      │
│                                 │
│  📱 4G USB-STICK:               │
│  • Einfach in USB-Port stecken │
│                                 │
│  🔋 POWERBANK:                  │
│  • USB-C Kabel zum Pi          │
└─────────────────────────────────┘

VERKABELUNG CHECKLIST:
☐ Servo: 3 Kabel (Rot→5V, Braun→GND, Orange→GPIO18)
☐ LEDs: 3x LED mit Widerständen
☐ 4G-Stick: In USB-Port eingesteckt
☐ Power: USB-C von PowerBank zu Pi
☐ Alle Verbindungen fest
```

### **2️⃣ RASPBERRY PI OS INSTALLIEREN (20 Minuten)**

#### **💾 SD-KARTE VORBEREITEN:**
```bash
1. Raspberry Pi Imager herunterladen:
   https://www.raspberrypi.org/software/

2. SD-Karte (32GB) in Computer stecken

3. Raspberry Pi OS Lite (64-bit) flashen
   • OS auswählen: "Raspberry Pi OS Lite"
   • Einstellungen konfigurieren (⚙️):
     - SSH aktivieren
     - Benutzername: pi
     - Passwort: parking123 (oder eigenes)
     - WiFi konfigurieren (optional)
   
4. SD-Karte in Pi einsetzen

5. Pi starten (grüne LED sollte blinken)

6. SSH-Verbindung testen:
   ssh pi@raspberrypi.local
   (oder IP-Adresse finden: nmap -sn 192.168.1.0/24)
```

### **3️⃣ SOFTWARE INSTALLIEREN (15 Minuten)**

#### **🐍 PYTHON SETUP:**
```bash
# 1. Per SSH am Pi anmelden
ssh pi@raspberrypi.local

# 2. Setup-Script ausführbar machen
chmod +x setup_pi.sh

# 3. Setup ausführen
./setup_pi.sh

# 4. Nach Installation: Neustart
sudo reboot
```

#### **📁 PROJEKT-DATEIEN KOPIEREN:**
```bash
# Auf deinem Computer (mit SCP):
scp parking_barrier.py pi@raspberrypi.local:/home/pi/smart_parking/
scp requirements.txt pi@raspberrypi.local:/home/pi/smart_parking/

# Oder via SSH am Pi:
cd /home/pi/smart_parking
# Dateien hier hinein kopieren/erstellen
```

### **4️⃣ 4G USB-STICK KONFIGURIEREN (10 Minuten)**

#### **📱 SIM-KARTE & NETZWERK:**
```bash
# 1. Nano-SIM in Huawei E3372 einsetzen
# 2. USB-Stick in Pi stecken
# 3. Stick erkennung prüfen:
lsusb | grep Huawei

# 4. Netzwerk-Verbindung einrichten:
sudo nmcli connection add type gsm ifname '*' con-name "4G-Internet" \
     apn "internet" user "" password ""

# 5. Verbindung aktivieren:
sudo nmcli connection up "4G-Internet"

# 6. Status prüfen:
nmcli device status
ip route show

# 7. Internet testen:
ping -c 3 google.com
```

### **5️⃣ BACKEND-URL KONFIGURIEREN**

#### **🔗 API-VERBINDUNG EINRICHTEN:**
```bash
# 1. parking_barrier.py bearbeiten:
nano /home/pi/smart_parking/parking_barrier.py

# 2. Zeile 31 anpassen:
API_BASE_URL = "https://deine-domain.com"  # Deine FastAPI URL

# 3. Device ID anpassen (optional):
DEVICE_ID = "PROTOTYPE_ZH_001"  # Unique per Gerät

# 4. Speichern: Ctrl+X, Y, Enter
```

### **6️⃣ ERSTEN TEST DURCHFÜHREN (5 Minuten)**

#### **🧪 MANUELLER TEST:**
```bash
# 1. Test-Modus starten:
cd /home/pi/smart_parking
python3 parking_barrier.py

# ERWARTETE AUSGABE:
# 🍓 Smart Parking Barrier - Raspberry Pi Controller
# 📍 Device ID: PROTOTYPE_ZH_001
# 🌐 Backend URL: https://deine-domain.com
# ✅ GPIO Pins erfolgreich konfiguriert
# ✅ Servo erfolgreich initialisiert (Position: DOWN)
# 🚀 Hauptschleife gestartet
# 💓 Heartbeat erfolgreich gesendet

# 2. LEDs prüfen:
# • Grüne LED: System läuft
# • Servo: Sollte in "DOWN" Position sein

# 3. Test stoppen: Ctrl+C
```

#### **🔧 HARDWARE-TEST:**
```bash
# GPIO Status prüfen:
gpio readall

# Servo-Test (manuell):
python3 -c "
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
servo = GPIO.PWM(18, 50)
servo.start(0)
servo.ChangeDutyCycle(2.5)  # DOWN
time.sleep(1)
servo.ChangeDutyCycle(12.5) # UP
time.sleep(1)
servo.ChangeDutyCycle(2.5)  # DOWN
time.sleep(1)
servo.stop()
GPIO.cleanup()
print('Servo-Test abgeschlossen!')
"
```

### **7️⃣ AUTOSTART AKTIVIEREN**

#### **🚀 SYSTEMD SERVICE:**
```bash
# 1. Service starten:
sudo systemctl start parking-barrier

# 2. Status prüfen:
sudo systemctl status parking-barrier

# 3. Logs anzeigen:
journalctl -u parking-barrier -f

# 4. Bei Problemen Service stoppen:
sudo systemctl stop parking-barrier

# 5. Service neu starten:
sudo systemctl restart parking-barrier
```

---

## 🔧 **TROUBLESHOOTING**

### **❌ HÄUFIGE PROBLEME:**

#### **Problem: GPIO Permission Denied**
```bash
# Lösung:
sudo usermod -a -G gpio pi
sudo reboot
```

#### **Problem: 4G-Stick wird nicht erkannt**
```bash
# Prüfen:
lsusb
dmesg | tail -20

# NetworkManager neu starten:
sudo systemctl restart NetworkManager
```

#### **Problem: Servo bewegt sich nicht**
```bash
# Verkabelung prüfen:
gpio readall
# Pin 12 (GPIO18) sollte PWM-fähig sein

# Servo-Power prüfen (5V Rail):
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
p = GPIO.PWM(18, 50)
p.start(7.5)  # Neutral position
input('Press Enter to stop...')
p.stop()
GPIO.cleanup()
"
```

#### **Problem: Backend-Verbindung fehlschlägt**
```bash
# Internet testen:
ping google.com

# API testen:
curl -X GET "https://deine-domain.com/api/barrier/PROTOTYPE_ZH_001/command"

# Logs prüfen:
tail -f /home/pi/parking_barrier.log
```

---

## 📊 **MONITORING & WARTUNG**

### **🔍 SYSTEM-ÜBERWACHUNG:**
```bash
# Service Status:
systemctl status parking-barrier

# Live Logs:
journalctl -u parking-barrier -f

# System-Performance:
htop
free -h
df -h

# GPIO Status:
gpio readall

# 4G Verbindung:
nmcli device status
```

### **🔄 UPDATES:**
```bash
# Software Updates:
cd /home/pi/smart_parking
git pull  # Falls Git-Repository
sudo systemctl restart parking-barrier

# System Updates:
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## 🎯 **NEXT STEPS NACH INSTALLATION:**

1. **✅ Hardware-Test** - Alle LEDs und Servo testen
2. **🌐 Backend-Integration** - API-Verbindung verifizieren  
3. **📱 Mobile App Test** - Bügel über App steuern
4. **🔋 Power-Test** - Laufzeit mit PowerBank messen
5. **📍 Outdoor-Test** - Wetterfestigkeit prüfen

**🎉 HERZLICHEN GLÜCKWUNSCH! Du hast einen funktionsfähigen Smart Parking Prototyp! 🚗**
