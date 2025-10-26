#!/bin/bash

# ParkSmart (Sesam) Backup Script
# Erstellt von: GitHub Copilot
# Datum: $(date +%Y-%m-%d)

set -e  # Exit on any error

# Konfiguration
SOURCE_DIR="/Users/albertgashi/Desktop/xyz/sesam"
BACKUP_BASE_DIR="/Users/albertgashi/Desktop/backups"
PROJECT_NAME="sesam"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE_DIR}/${PROJECT_NAME}_backup_${TIMESTAMP}"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ParkSmart Backup Script${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Überprüfe ob Quellverzeichnis existiert
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Fehler: Quellverzeichnis nicht gefunden: $SOURCE_DIR${NC}"
    exit 1
fi

# Erstelle Backup-Verzeichnis
echo -e "${YELLOW}📁 Erstelle Backup-Verzeichnis...${NC}"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✅ Backup-Verzeichnis erstellt: $BACKUP_DIR${NC}"

# Kopiere Projektdateien
echo -e "${YELLOW}📋 Kopiere Projektdateien...${NC}"
cp -R "$SOURCE_DIR" "$BACKUP_DIR/"
echo -e "${GREEN}✅ Projektdateien kopiert${NC}"

# Erstelle Backup-Info-Datei
echo -e "${YELLOW}📝 Erstelle Backup-Informationen...${NC}"
cat > "$BACKUP_DIR/backup_info.txt" << EOF
ParkSmart (Sesam) Backup Information
====================================

Backup erstellt am: $(date)
Quellverzeichnis: $SOURCE_DIR
Backup-Verzeichnis: $BACKUP_DIR

Projekt-Details:
- Name: ParkSmart
- Backend: FastAPI mit MongoDB
- Frontend: React mit Tailwind CSS
- Mapping: React-Leaflet
- Datenbank: MongoDB (test_database)

Test-Benutzer verfügbar:
- user@test.com / password123 (User)
- owner@test.com / password123 (Owner)
- admin@test.com / password123 (Admin)

Start-Kommandos:
Backend: cd backend && uvicorn server:app --reload
Frontend: cd frontend && npm start

Ports:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
EOF

echo -e "${GREEN}✅ Backup-Informationen erstellt${NC}"

# Komprimiere das Backup
echo -e "${YELLOW}🗜️  Komprimiere Backup...${NC}"
cd "$BACKUP_BASE_DIR"
tar -czf "${PROJECT_NAME}_backup_${TIMESTAMP}.tar.gz" "${PROJECT_NAME}_backup_${TIMESTAMP}"
echo -e "${GREEN}✅ Backup komprimiert${NC}"

# Zeige Backup-Zusammenfassung
echo ""
echo -e "${BLUE}📊 Backup-Zusammenfassung${NC}"
echo -e "${BLUE}========================${NC}"
echo -e "Backup-Verzeichnis: ${GREEN}$BACKUP_DIR${NC}"
echo -e "Komprimiertes Backup: ${GREEN}${BACKUP_BASE_DIR}/${PROJECT_NAME}_backup_${TIMESTAMP}.tar.gz${NC}"
echo ""
echo -e "${GREEN}✅ Backup erfolgreich erstellt!${NC}"
EOF
