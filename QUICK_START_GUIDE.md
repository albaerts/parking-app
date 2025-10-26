# 🚀 Parking App - Quick Start Guide

## Sofort loslegen in 3 Schritten:

### 1️⃣ Backend starten
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

### 2️⃣ Frontend starten (neues Terminal)
```bash
cd frontend
npm install
npm start
```

### 3️⃣ App öffnen
Browser: `http://localhost:3000`

## 👥 Test-Accounts erstellen
```bash
# User Account
Email: user@test.com
Password: password123
Role: user

# Owner Account  
Email: owner@test.com
Password: password123
Role: owner
```

## 🎯 Features testen:

### Als User:
1. 🗺️ **Find Parking** - Karte erkunden
2. 📝 **Booking History** - Buchungen verwalten
3. ⭐ **Bewertungen** - Spots bewerten
4. 👤 **Account** - Profil verwalten

### Als Owner:
1. 🗺️ **Meine Spots** - Parkplätze hinzufügen
2. 📝 **Bookings** - Einnahmen ansehen
3. ⭐ **Bewertungen** - Kunden bewerten
4. 👤 **Account** - Business Stats

## 🔍 Address Search testen:
- "migros" → findet alle Migros-Filialen
- "bistro" → findet Restaurants
- "tech" → findet ETH, Startups
- "tattoo" → findet Studios

## 💰 Price Recommendations:
Beim Hinzufügen neuer Spots automatische Preisvorschläge basierend auf der Umgebung.

## 🔧 Troubleshooting:
- MongoDB läuft? `brew services start mongodb-community`
- Ports frei? 3000 (Frontend), 8000 (Backend)
- Node.js installiert? `node --version`
- Python 3.8+? `python --version`

**Happy Parking! 🚗🅿️**
