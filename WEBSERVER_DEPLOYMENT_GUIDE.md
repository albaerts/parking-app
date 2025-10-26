# 🌐 **PARKING APP AUF WEBSERVER DEPLOYEN**

## 🎯 **DEINE APP FÜR ANDERE VERFÜGBAR MACHEN**

### **📋 VORAUSSETZUNGEN:**
- ✅ Dein Webserver mit SSH-Zugang
- ✅ Node.js & npm installiert
- ✅ Python 3.9+ installiert  
- ✅ Domain/Subdomain (z.B. parking.deinedomain.ch)

---

## 🚀 **DEPLOYMENT-STRATEGIE:**

### **🏗️ ARCHITEKTUR:**
```bash
FRONTEND (React):     https://parking.deinedomain.ch
BACKEND (FastAPI):    https://parking.deinedomain.ch/api
DATABASE (SQLite):    Auf deinem Server
REVERSE PROXY:        Nginx (empfohlen)
```

---

## 📦 **SCHRITT 1: FRONTEND VORBEREITEN**

### **🔧 REACT APP FÜR PRODUCTION BUILDEN:**
```bash
cd frontend

# Dependencies installieren
npm install

# Production Build erstellen
npm run build

# Build-Ordner wird erstellt: frontend/build/
```

### **⚙️ FRONTEND KONFIGURATION ANPASSEN:**
```javascript
// frontend/src/App.js - API URL anpassen
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://parking.deinedomain.ch/api'  // Deine Domain!
  : 'http://localhost:8000';

// Geolocation Fallback für Tester ohne GPS
const DEMO_LOCATION = {
  lat: 47.3769,  // Zürich Koordinaten
  lng: 8.5417
};
```

---

## 🐍 **SCHRITT 2: BACKEND VORBEREITEN**

### **📝 REQUIREMENTS.TXT ERWEITERN:**
```bash
# backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
sqlalchemy==2.0.23
python-dotenv==1.0.0
gunicorn==21.2.0  # Für Production
```

### **🔧 PRODUCTION KONFIGURATION:**
```python
# backend/.env (auf Server erstellen)
DATABASE_URL=sqlite:///./parking.db
SECRET_KEY=dein-super-sicherer-secret-key-hier  # Generiere einen neuen!
ALLOWED_ORIGINS=["https://parking.deinedomain.ch"]
DEBUG=False
```

### **🚀 GUNICORN KONFIGURATION:**
```python
# backend/gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 60
max_requests = 1000
max_requests_jitter = 100
```

---

## 🖥️ **SCHRITT 3: SERVER SETUP**

### **📂 ORDNERSTRUKTUR AUF SERVER:**
```bash
/var/www/parking/
├── frontend/           # React Build
│   ├── build/         # npm run build Output
│   └── static/
├── backend/           # FastAPI App
│   ├── server.py
│   ├── requirements.txt
│   └── .env
└── nginx/            # Nginx Konfiguration
```

### **🔄 DEPLOYMENT BEFEHLE:**
```bash
# Auf deinem Server via SSH:

# 1. Ordner erstellen
sudo mkdir -p /var/www/parking
sudo chown $USER:$USER /var/www/parking
cd /var/www/parking

# 2. Code hochladen (verschiedene Optionen):

# OPTION A: Git Clone (empfohlen)
git clone https://github.com/dein-username/parking-app.git .

# OPTION B: SCP Upload
# Lokal ausführen:
scp -r frontend/build/ user@server:/var/www/parking/frontend/
scp -r backend/ user@server:/var/www/parking/

# OPTION C: FTP/SFTP mit FileZilla

# 3. Backend Setup
cd /var/www/parking/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Datenbank initialisieren
python server.py --init-db
```

---

## 🔧 **SCHRITT 4: NGINX KONFIGURATION**

### **📝 NGINX SITE CONFIG:**
```nginx
# /etc/nginx/sites-available/parking
server {
    listen 80;
    server_name parking.deinedomain.ch;  # Deine Domain ändern!

    # Frontend (React Build)
    location / {
        root /var/www/parking/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Caching für statische Assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support (falls nötig)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### **🔐 SSL ZERTIFIKAT (Let's Encrypt):**
```bash
# Certbot installieren und SSL einrichten
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d parking.deinedomain.ch

# Automatische Erneuerung
sudo crontab -e
# Hinzufügen: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔧 **SCHRITT 5: SYSTEMD SERVICE (AUTO-START)**

### **📝 SERVICE DATEI:**
```ini
# /etc/systemd/system/parking-api.service
[Unit]
Description=Parking App FastAPI
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/parking/backend
Environment=PATH=/var/www/parking/backend/venv/bin
ExecStart=/var/www/parking/backend/venv/bin/gunicorn server:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **🚀 SERVICE AKTIVIEREN:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable parking-api
sudo systemctl start parking-api
sudo systemctl status parking-api

# Nginx neustarten
sudo systemctl restart nginx
```

---

## 🧪 **SCHRITT 6: TESTEN & DEMO DATEN**

### **📊 DEMO PARKPLÄTZE ERSTELLEN:**
```python
# backend/create_demo_data.py
import sqlite3

demo_spots = [
    {"name": "Bahnhofstrasse 1", "lat": 47.3769, "lng": 8.5417, "status": "free"},
    {"name": "Limmatquai 50", "lat": 47.3732, "lng": 8.5448, "status": "occupied"},  
    {"name": "Paradeplatz", "lat": 47.3696, "lng": 8.5399, "status": "free"},
    {"name": "ETH Zentrum", "lat": 47.3767, "lng": 8.5482, "status": "free"},
    {"name": "Opernhaus", "lat": 47.3651, "lng": 8.5450, "status": "occupied"}
]

# In Datenbank einfügen
conn = sqlite3.connect('/var/www/parking/backend/parking.db')
for spot in demo_spots:
    conn.execute("""
        INSERT INTO parking_spots (name, latitude, longitude, status) 
        VALUES (?, ?, ?, ?)
    """, (spot["name"], spot["lat"], spot["lng"], spot["status"]))
conn.commit()
```

### **🌍 BENUTZER-ACCOUNTS FÜR TESTER:**
```python
# Demo-Accounts erstellen
demo_users = [
    {"username": "demo", "password": "demo123"},
    {"username": "tester", "password": "test123"},
    {"username": "admin", "password": "admin123"}
]
```

---

## 🔍 **SCHRITT 7: MONITORING & LOGS**

### **📊 LOG ÜBERWACHUNG:**
```bash
# Backend Logs anschauen
sudo journalctl -u parking-api -f

# Nginx Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Performance Monitoring
htop  # Server Auslastung
```

---

## 🎯 **DEPLOYMENT CHECKLISTE:**

### **✅ FRONTEND:**
```bash
☐ npm run build erfolgreich
☐ API_BASE_URL auf Production Domain gesetzt
☐ Build-Ordner nach /var/www/parking/frontend/ kopiert
☐ Nginx serviert Frontend korrekt
```

### **✅ BACKEND:**
```bash
☐ requirements.txt installiert
☐ .env Datei mit SECRET_KEY erstellt
☐ Datenbank initialisiert
☐ Gunicorn Service läuft
☐ API über /api erreichbar
```

### **✅ INFRASTRUKTUR:**
```bash
☐ Domain zeigt auf deinen Server
☐ Nginx Konfiguration aktiv
☐ SSL Zertifikat installiert (HTTPS)
☐ Systemd Service aktiviert
☐ Demo-Daten eingefügt
```

---

## 🚀 **SCHNELL-DEPLOYMENT SCRIPT:**

```bash
#!/bin/bash
# deploy.sh - Automatisches Deployment

# Frontend builden
cd frontend && npm run build

# Zum Server uploaden
scp -r build/ user@deinserver.ch:/var/www/parking/frontend/
scp -r ../backend/ user@deinserver.ch:/var/www/parking/

# Backend auf Server neustarten
ssh user@deinserver.ch "
  cd /var/www/parking/backend
  source venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart parking-api
"

echo "🎉 Deployment erfolgreich! App verfügbar unter: https://parking.deinedomain.ch"
```

---

## 🌍 **FINAL: DEINE APP LIVE!**

**Nach dem Deployment ist deine App erreichbar unter:**
- **Frontend:** `https://parking.deinedomain.ch`
- **API:** `https://parking.deinedomain.ch/api/docs`

**Demo-Logins für Tester:**
- Username: `demo` / Password: `demo123`
- Username: `tester` / Password: `test123`

**Features für Benutzer:**
- ✅ Live-Parkplatz Suche
- ✅ Distanz-basierte Sortierung  
- ✅ Echtzeit-Status Updates
- ✅ Responsive Design (Mobile/Desktop)

**Willst du mit dem Deployment anfangen?** 🚀
