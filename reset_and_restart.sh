#!/bin/bash

# Skript zum Zurücksetzen der Testumgebung

echo "🚀 Starte Reset-Prozess..."

# 1. Testbenutzer löschen
echo "🗑️  Lösche Testbenutzer aus der Datenbank..."
python3 delete_user.py

# 2. Laufende Server beenden
echo "🛑 Beende laufende Server..."
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
echo "✅ Server erfolgreich beendet."

# Kurze Pause, um sicherzustellen, dass die Ports freigegeben sind
sleep 2

# 3. Server neu starten
echo "🚀 Starte Server neu..."

# Backend-Server im Hintergrund starten
echo "   - Starte Backend-Server auf Port 8000..."
/Users/albertgashi/Desktop/Parking_App_BACKUP_20250730_231235/.venv-1/bin/python -m uvicorn backend.server_gashis:app --reload --port 8000 > backend.log 2>&1 &

# Frontend-Server im Hintergrund starten
echo "   - Starte Frontend-Server auf Port 3000..."
npm --prefix frontend start > frontend.log 2>&1 &

sleep 5 # Warte kurz, damit die Server hochfahren können

echo "✅ Reset abgeschlossen! Die Anwendung sollte in Kürze unter http://localhost:3000 verfügbar sein."
echo "🪵 Logs werden in backend.log und frontend.log geschrieben."
