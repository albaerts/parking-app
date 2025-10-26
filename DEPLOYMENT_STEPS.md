# 🚀 **GASHIS.CH DEPLOYMENT - STEP BY STEP**

## ✅ **ZUGANGSDATEN BEREIT:**
- **Server:** server17.hostfactory.ch
- **Username:** ftpalbertgashi  
- **Passwort:** [gespeichert]

---

## 📦 **SCHRITT 1: SCP UPLOAD (DIREKT VOM MAC)**

### **🎨 FRONTEND HOCHLADEN:**
```bash
# Im Terminal ausführen:
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend

# Frontend Build hochladen
scp -r build/* ftpalbertgashi@server17.hostfactory.ch:~/htdocs/
```

### **🐍 BACKEND HOCHLADEN:**
```bash
# Backend-Dateien hochladen
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/backend

# Server-Datei hochladen
scp server_gashis.py ftpalbertgashi@server17.hostfactory.ch:~/htdocs/api/server.py

# Requirements hochladen
scp requirements_simple.txt ftpalbertgashi@server17.hostfactory.ch:~/htdocs/api/requirements.txt
```

---

## 🔧 **SCHRITT 2: SSH SETUP**

### **🔗 SSH-VERBINDUNG:**
```bash
ssh ftpalbertgashi@server17.hostfactory.ch
```

### **📁 ORDNER ERSTELLEN:**
```bash
# Nach SSH-Verbindung:
cd htdocs
mkdir -p api

# .htaccess erstellen
cat > .htaccess << 'EOF'
RewriteEngine On

# API Routes zu Python Backend (Port 8001)
RewriteRule ^api/(.*)$ http://127.0.0.1:8001/$1 [P,L,QSA]
RewriteRule ^api$ http://127.0.0.1:8001/ [P,L]

# Frontend SPA Routing
RewriteCond %{REQUEST_URI} !^/api/
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]

# HTTPS Redirect
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
EOF
```

### **🐍 PYTHON BACKEND SETUP:**
```bash
cd ~/htdocs/api

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# API starten
gunicorn server:app --bind 127.0.0.1:8001 --daemon --pid /tmp/parking_api.pid

# Status prüfen
ps aux | grep gunicorn | grep 8001
```

---

## 🧪 **SCHRITT 3: TESTEN**

### **🌍 LIVE-TEST:**
```bash
# API Health Check
curl http://127.0.0.1:8001/
# → Sollte JSON mit "Gashis Parking API ist online!" zeigen

# Parkplätze testen
curl http://127.0.0.1:8001/parking-spots
# → Sollte Liste mit Schweizer Parkplätzen zeigen
```

---

## 🎉 **RESULT:**
**Nach dem Setup ist deine App erreichbar unter:**
- **https://gashis.ch** (Frontend)
- **https://gashis.ch/api** (Backend API)

---

**Bereit für den Upload?** 🚀
