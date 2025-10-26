# 📋 **GASHIS.CH DEPLOYMENT - COPY & PASTE BEFEHLE**

## ✅ **ALLE DATEIEN SIND BEREIT:**
- ✅ Frontend Build erstellt
- ✅ Backend für gashis.ch angepasst
- ✅ Zugangsdaten: server17.hostfactory.ch

---

## 🚀 **SCHRITT-FÜR-SCHRITT COMMANDS:**

### **1️⃣ FRONTEND UPLOAD:**
```bash
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/frontend
scp -r build/* ftpalbertgashi@server17.hostfactory.ch:~/htdocs/
```

### **2️⃣ BACKEND UPLOAD:**
```bash
cd /Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/backend
scp server_gashis.py ftpalbertgashi@server17.hostfactory.ch:~/htdocs/api/server.py
scp requirements_simple.txt ftpalbertgashi@server17.hostfactory.ch:~/htdocs/api/requirements.txt
```

### **3️⃣ SSH-VERBINDUNG:**
```bash
ssh ftpalbertgashi@server17.hostfactory.ch
```

### **4️⃣ SERVER SETUP (auf Hostfactory):**
```bash
cd htdocs
mkdir -p api

# .htaccess erstellen
cat > .htaccess << 'EOF'
RewriteEngine On
RewriteRule ^api/(.*)$ http://127.0.0.1:8001/$1 [P,L,QSA]
RewriteRule ^api$ http://127.0.0.1:8001/ [P,L]
RewriteCond %{REQUEST_URI} !^/api/
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
EOF

# Python Backend Setup
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn server:app --bind 127.0.0.1:8001 --daemon
```

### **5️⃣ TESTEN:**
```bash
curl http://127.0.0.1:8001/
```

---

## 🎯 **BEREIT ZUM STARTEN?**

**Sag "ja" und ich führe die Befehle Schritt für Schritt aus!** 🚀
