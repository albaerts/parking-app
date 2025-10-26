# 🚀 **PARKING APP AUF GASHIS.CH DEPLOYEN**

## 🎯 **DEINE DOMAIN: GASHIS.CH**

### **🌐 FINAL URLS:**
- **Frontend:** `https://gashis.ch/parking` oder `https://parking.gashis.ch`
- **API:** `https://gashis.ch/parking/api` 
- **Admin:** `https://gashis.ch/parking/api/docs`

---

## 📦 **SCHRITT 1: FRONTEND VORBEREITEN**

### **⚙️ APP.JS FÜR GASHIS.CH ANPASSEN:**
```javascript
// frontend/src/App.js
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://gashis.ch/parking/api'  // Deine Domain!
  : 'http://localhost:8000';

// Schweizer Demo-Location (Zürich)
const DEMO_LOCATION = {
  lat: 47.3769,  // Zürich Hauptbahnhof
  lng: 8.5417
};

// Geolocation mit Zürich Fallback
const getCurrentLocation = () => {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.log('Geolocation failed, using Zürich fallback');
          resolve(DEMO_LOCATION);
        }
      );
    } else {
      resolve(DEMO_LOCATION);
    }
  });
};
```

### **🏗️ REACT BUILD ERSTELLEN:**
```bash
# Im Terminal auf deinem Mac:
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend

# Dependencies installieren
npm install

# Production Build für gashis.ch
npm run build

# → Erstellt frontend/build/ Ordner
```

---

## 🐍 **SCHRITT 2: BACKEND FÜR GASHIS.CH ANPASSEN**

### **📝 SERVER.PY MIT GASHIS.CH CORS:**
```python
# backend/server.py - Angepasst für gashis.ch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Gashis Parking API",
    description="Smart Parking System für die Schweiz",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS für gashis.ch
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gashis.ch",
        "https://www.gashis.ch", 
        "https://parking.gashis.ch",  # Falls Subdomain
        "http://localhost:3000"        # Für lokale Entwicklung
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Path für Hostfactory
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "parking.db")

@app.get("/")
async def root():
    return {
        "message": "Gashis Parking API ist online! 🚗",
        "domain": "gashis.ch",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Hier kommt deine bestehende API Logic...
# (Alle deine Routes von server.py)
```

---

## 🔧 **SCHRITT 3: HOSTFACTORY DEPLOYMENT**

### **📂 SSH-VERBINDUNG ZU GASHIS.CH:**
```bash
# Im Terminal auf deinem Mac:
ssh deinusername@ssh.hostfactory.ch

# Erfolgreich? Dann weiter!
# Falls Fehler: Username in my.hostfactory.ch checken
```

### **📁 ORDNERSTRUKTUR EINRICHTEN:**
```bash
# Via SSH auf Hostfactory Server:
cd htdocs

# Parking-App Ordner erstellen
mkdir -p parking
mkdir -p parking/api

# Übersicht der Struktur:
# htdocs/
# ├── parking/           # Deine Parking App
# │   ├── index.html     # React Frontend
# │   ├── static/        # CSS, JS Files
# │   └── api/           # Python Backend
# └── (andere Websites)
```

---

## 📤 **SCHRITT 4: DATEIEN HOCHLADEN**

### **🚀 FRONTEND UPLOAD:**
```bash
# OPTION A: SCP vom Mac (empfohlen)
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend
scp -r build/* deinusername@ssh.hostfactory.ch:~/htdocs/parking/

# OPTION B: Via SSH auf Server
# (falls du build/ per FTP hochgeladen hast)
# cd ~/htdocs && cp -r temp_build/* parking/
```

### **🐍 BACKEND UPLOAD:**
```bash
# SCP Backend-Dateien
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235
scp -r backend/* deinusername@ssh.hostfactory.ch:~/htdocs/parking/api/

# Wichtige Dateien checken:
# - server.py
# - requirements.txt  
# - (weitere .py Dateien)
```

---

## 🔧 **SCHRITT 5: PYTHON ENVIRONMENT SETUP**

### **🐍 BACKEND KONFIGURATION:**
```bash
# Via SSH auf Hostfactory:
cd ~/htdocs/parking/api

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Requirements installieren
pip install fastapi uvicorn python-jose passlib sqlalchemy python-dotenv gunicorn

# Gunicorn Config erstellen
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8001"  # Port 8001 für gashis.ch
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
max_requests = 500
daemon = False
EOF
```

### **💾 DATABASE INITIALISIEREN:**
```python
# Via SSH: Python-Shell öffnen
python3 << EOF
import sqlite3

# Database erstellen
conn = sqlite3.connect('parking.db')

# Parkplätze Table
conn.execute('''
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        status TEXT DEFAULT 'free',
        price_per_hour REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Demo-Daten für die Schweiz
demo_spots = [
    ("Zürich HB Parkhaus Sihlquai", "Sihlquai 41, 8005 Zürich", 47.3769, 8.5417, "free", 4.50),
    ("Basel SBB Centralbahnplatz", "Centralbahnpl. 20, 4051 Basel", 47.5474, 7.5892, "occupied", 3.80),
    ("Bern Bahnhof Parking", "Bahnhofplatz 10A, 3011 Bern", 46.9481, 7.4474, "free", 4.20),
    ("Genève Aéroport P51", "Route de l'Aéroport 21, 1215 Genève", 46.2044, 6.1432, "free", 5.00),
    ("Luzern Parkhaus Bahnhof", "Bahnhofstrasse 3, 6003 Luzern", 47.0502, 8.3093, "free", 3.90)
]

for spot in demo_spots:
    conn.execute('''
        INSERT INTO parking_spots (name, address, latitude, longitude, status, price_per_hour)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', spot)

conn.commit()
conn.close()
print("✅ Database und Demo-Daten erstellt!")
EOF
```

---

## 🌐 **SCHRITT 6: HTACCESS FÜR GASHIS.CH**

### **📝 .HTACCESS KONFIGURATION:**
```apache
# htdocs/parking/.htaccess
RewriteEngine On

# API Routes zu Python Backend (Port 8001)
RewriteRule ^api/(.*)$ http://127.0.0.1:8001/$1 [P,L,QSA]
RewriteRule ^api$ http://127.0.0.1:8001/ [P,L]

# Frontend SPA Routing
RewriteCond %{REQUEST_URI} !^/parking/api/
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /parking/index.html [L]

# HTTPS Redirect für gashis.ch
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Cache-Control für Performance
<FilesMatch "\.(js|css|png|jpg|jpeg|gif|ico|svg)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 year"
    Header append Cache-Control "public, immutable"
</FilesMatch>

# GZIP Kompression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>
```

---

## 🚀 **SCHRITT 7: BACKEND STARTEN**

### **📜 START-SCRIPT ERSTELLEN:**
```bash
# Via SSH: Start-Script erstellen
cd ~/htdocs/parking/api
cat > start_parking.sh << EOF
#!/bin/bash
cd /home/deinusername/htdocs/parking/api
source venv/bin/activate
gunicorn server:app -c gunicorn.conf.py --daemon --pid /tmp/parking_api.pid
echo "✅ Gashis Parking API gestartet auf Port 8001"
EOF

chmod +x start_parking.sh
```

### **🔄 API STARTEN:**
```bash
# API starten
./start_parking.sh

# Status prüfen
ps aux | grep gunicorn | grep 8001

# Falls Neustart nötig:
pkill -f "gunicorn.*8001"
./start_parking.sh
```

---

## 🔐 **SCHRITT 8: SSL FÜR GASHIS.CH AKTIVIEREN**

### **📜 LET'S ENCRYPT SSL:**
```bash
# In deinem Hostfactory cPanel:
1. 🌐 my.hostfactory.ch → Login
2. 🔒 SSL/TLS → Let's Encrypt
3. 🎯 Domain wählen: gashis.ch
4. ✅ "SSL Zertifikat installieren"
5. 🔄 Auto-Renewal aktivieren

→ https://gashis.ch läuft automatisch!
```

---

## 🧪 **SCHRITT 9: DEPLOYMENT TESTEN**

### **📝 GASHIS.CH TEST-SCRIPT:**
```python
# test_gashis_deployment.py (lokal ausführen)
import requests
import json

BASE_URL = "https://gashis.ch/parking"
print("🧪 Testing Gashis Parking App...")

# Test 1: Frontend
try:
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        print("✅ Frontend erreichbar: https://gashis.ch/parking")
    else:
        print(f"❌ Frontend Error: {response.status_code}")
except Exception as e:
    print(f"❌ Frontend nicht erreichbar: {e}")

# Test 2: API Health
try:
    response = requests.get(f"{BASE_URL}/api/")
    if response.status_code == 200:
        data = response.json()
        print("✅ API erreichbar: https://gashis.ch/parking/api")
        print(f"   Message: {data.get('message', 'N/A')}")
    else:
        print(f"❌ API Error: {response.status_code}")
except Exception as e:
    print(f"❌ API nicht erreichbar: {e}")

# Test 3: Parkplätze
try:
    response = requests.get(f"{BASE_URL}/api/parking-spots")
    if response.status_code == 200:
        spots = response.json()
        print(f"✅ Parkplätze geladen: {len(spots)} Schweizer Spots")
        for spot in spots[:3]:
            print(f"   🚗 {spot['name']}: {spot['status']} (CHF {spot['price_per_hour']}/h)")
    else:
        print(f"❌ Parkplätze Error: {response.status_code}")
except Exception as e:
    print(f"❌ Parkplätze nicht verfügbar: {e}")

# Test 4: API Docs
try:
    response = requests.get(f"{BASE_URL}/api/docs")
    if response.status_code == 200:
        print("✅ API Dokumentation: https://gashis.ch/parking/api/docs")
    else:
        print(f"❌ API Docs Error: {response.status_code}")
except:
    print("❌ API Docs nicht erreichbar")

print("\n🎉 Gashis.ch Parking App Deployment Test abgeschlossen!")
```

---

## ✅ **DEPLOYMENT CHECKLISTE GASHIS.CH:**

### **🖥️ SERVER:**
```bash
☐ SSH-Verbindung zu Hostfactory funktioniert
☐ Ordner ~/htdocs/parking/ erstellt
☐ Python venv in ~/htdocs/parking/api/ installiert
☐ Gunicorn läuft auf Port 8001
☐ SQLite Database mit Schweizer Demo-Daten
```

### **🌐 FRONTEND:**
```bash
☐ npm run build erfolgreich ausgeführt
☐ React-Dateien nach ~/htdocs/parking/ hochgeladen
☐ API_BASE_URL = 'https://gashis.ch/parking/api' gesetzt
☐ .htaccess für SPA-Routing konfiguriert
```

### **🔗 INTEGRATION:**
```bash
☐ CORS in server.py für gashis.ch konfiguriert
☐ SSL Zertifikat für gashis.ch aktiv
☐ API-Proxy via .htaccess funktioniert
☐ https://gashis.ch/parking lädt
☐ https://gashis.ch/parking/api antwortet
```

---

## 🎯 **COPY-PASTE DEPLOYMENT COMMANDS:**

### **📋 KOMPLETTE BEFEHLSFOLGE:**
```bash
# 1. SSH-Verbindung
ssh deinusername@ssh.hostfactory.ch

# 2. Ordner erstellen
cd htdocs && mkdir -p parking/api

# 3. Backend Setup (auf Server)
cd parking/api
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn gunicorn python-jose passlib sqlalchemy python-dotenv

# 4. Gunicorn Config
echo 'bind = "127.0.0.1:8001"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"' > gunicorn.conf.py

# 5. API starten
gunicorn server:app -c gunicorn.conf.py --daemon

# 6. Status prüfen  
ps aux | grep gunicorn
```

### **🚀 LOKALE BEFEHLE (auf Mac):**
```bash
# Frontend builden
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend
npm run build

# Dateien hochladen
scp -r build/* deinusername@ssh.hostfactory.ch:~/htdocs/parking/
scp -r ../backend/* deinusername@ssh.hostfactory.ch:~/htdocs/parking/api/
```

---

## 🎉 **GASHIS.CH PARKING APP LIVE!**

### **🌍 DEINE URLS:**
- **App:** `https://gashis.ch/parking`
- **API:** `https://gashis.ch/parking/api/docs`
- **Health:** `https://gashis.ch/parking/api/`

### **📱 FEATURES FÜR BENUTZER:**
- ✅ **Schweizer Parkplätze** (Zürich, Basel, Bern, Genf, Luzern)
- ✅ **Echtzeit-Status** (frei/besetzt)
- ✅ **GPS-basierte Suche** mit Zürich-Fallback
- ✅ **Preise pro Stunde** in CHF
- ✅ **Responsive Design** (Mobile + Desktop)
- ✅ **HTTPS Secure** mit Let's Encrypt

### **🔧 ADMIN FEATURES:**
- ✅ **API Dokumentation** unter `/api/docs`
- ✅ **Schweizer Demo-Daten** vorinstalliert
- ✅ **SQLite Database** für einfache Wartung

---

## 🚀 **BEREIT FÜR DEN START?**

**Führe diese Befehle aus und deine App ist live auf gashis.ch!**

**Brauchst du Hilfe bei einem Schritt?** Sag Bescheid! 🎯
