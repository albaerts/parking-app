#!/bin/bash
# Smart Parking Barrier - Raspberry Pi Setup Script
# Führe dieses Script nach dem Hardware-Aufbau aus

echo "🍓 Smart Parking Barrier - Pi Setup wird gestartet..."
echo "=================================================="

# System Updates
echo "📦 System wird aktualisiert..."
sudo apt update && sudo apt upgrade -y

# Python 3 und pip installieren (falls nicht vorhanden)
echo "🐍 Python 3 Setup..."
sudo apt install python3 python3-pip python3-venv -y

# GPIO-Bibliotheken installieren
echo "🔌 GPIO-Bibliotheken installieren..."
sudo apt install python3-rpi.gpio -y

# Virtuelle Umgebung erstellen
echo "📁 Virtuelle Python-Umgebung erstellen..."
cd /home/pi
python3 -m venv parking_env
source parking_env/bin/activate

# Python-Pakete installieren
echo "📚 Python-Pakete installieren..."
pip3 install RPi.GPIO requests

# Projekt-Ordner erstellen
echo "📂 Projekt-Ordner Setup..."
mkdir -p /home/pi/smart_parking
cd /home/pi/smart_parking

# 4G USB-Stick Konfiguration
echo "📱 4G USB-Stick wird konfiguriert..."

# NetworkManager für 4G-Verbindung installieren
sudo apt install network-manager -y

# USB-Stick automatisch erkennen
echo "🔍 4G USB-Stick suchen..."
lsusb | grep -i huawei

# PPP für 4G-Verbindung installieren
sudo apt install ppp -y

# Autostart-Service erstellen
echo "🚀 Autostart-Service erstellen..."
sudo tee /etc/systemd/system/parking-barrier.service > /dev/null <<EOF
[Unit]
Description=Smart Parking Barrier Controller
After=network.target
StartLimitBurst=5
StartLimitIntervalSec=10s

[Service]
Type=simple
Restart=always
RestartSec=5s
User=pi
WorkingDirectory=/home/pi/smart_parking
Environment=PATH=/home/pi/parking_env/bin
ExecStart=/home/pi/parking_env/bin/python /home/pi/smart_parking/parking_barrier.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren (aber noch nicht starten)
sudo systemctl enable parking-barrier.service

# Log-Datei Setup
echo "📝 Log-System Setup..."
touch /home/pi/parking_barrier.log
chmod 664 /home/pi/parking_barrier.log

# GPIO-Berechtigungen setzen
echo "🔐 GPIO-Berechtigungen setzen..."
sudo usermod -a -G gpio pi

# Firewall-Regeln (falls UFW aktiv)
echo "🔥 Firewall-Setup..."
if command -v ufw &> /dev/null; then
    sudo ufw allow out 80/tcp    # HTTP
    sudo ufw allow out 443/tcp   # HTTPS
    sudo ufw allow out 53        # DNS
fi

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "🔧 NÄCHSTE SCHRITTE:"
echo "1. Hardware verkabeln (siehe Anleitung)"
echo "2. parking_barrier.py in /home/pi/smart_parking/ kopieren"
echo "3. Backend-URL in parking_barrier.py anpassen"
echo "4. SIM-Karte in 4G-Stick einsetzen"
echo "5. Test starten: python3 parking_barrier.py"
echo "6. Service starten: sudo systemctl start parking-barrier"
echo ""
echo "📊 NÜTZLICHE BEFEHLE:"
echo "- Logs anzeigen: journalctl -u parking-barrier -f"
echo "- Service Status: systemctl status parking-barrier"
echo "- Hardware testen: gpio readall"
echo "- 4G Status: nmcli device status"
echo ""
echo "🎉 Happy Parking! 🚗"
