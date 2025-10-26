# ParkSmart Backup - $(date +%Y-%m-%d)

## 📋 Backup-Inhalt
Dieses Backup enthält das komplette ParkSmart-Projekt (Sesam) inklusive:

- ✅ **Backend** (FastAPI + MongoDB)
- ✅ **Frontend** (React + Tailwind CSS) 
- ✅ **Interaktive Karte** (React-Leaflet)
- ✅ **Authentifizierung** (JWT)
- ✅ **Admin-Dashboard**
- ✅ **Test-Daten** (19 Benutzer)

## 🔄 Wiederherstellung

### 1. Backend starten
```bash
cd sesam/backend
pip install -r requirements.txt
uvicorn server:app --reload
```

### 2. Frontend starten
```bash
cd sesam/frontend
npm install
npm start
```

### 3. MongoDB
Stelle sicher, dass MongoDB läuft und die Datenbank `test_database` verfügbar ist.

## 🔐 Test-Konten
- **User:** user@test.com / password123
- **Owner:** owner@test.com / password123  
- **Admin:** admin@test.com / password123

## ⚡ Funktionen
- 🗺️ Interaktive Karte mit Parkplätzen
- 👤 Benutzer-Verwaltung
- 🏢 Owner-Dashboard
- 👑 Admin-Panel
- 💳 Payment-Integration (Stripe)
- 📱 Responsive Design

## 🛠️ Technologie-Stack
- **Backend:** FastAPI, MongoDB, JWT, Stripe
- **Frontend:** React, Tailwind CSS, React-Leaflet
- **Karte:** OpenStreetMap mit Leaflet
- **Datenbank:** MongoDB

## 📁 Wichtige Dateien
- `backend/server.py` - Haupt-API-Server
- `frontend/src/App.js` - React-Hauptkomponente
- `frontend/src/App.css` - Styling inkl. Leaflet-Fixes
- `backend/requirements.txt` - Python-Abhängigkeiten
- `frontend/package.json` - Node.js-Abhängigkeiten

## 🌐 URLs nach Start
- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

## 📞 Support
Bei Fragen zum Backup oder zur Wiederherstellung kontaktieren Sie den Entwickler.
