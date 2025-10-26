#!/bin/bash

# ParkSmart Erweiterte Backup-Strategie
# Erstellt von: GitHub Copilot
# Datum: $(date +%Y-%m-%d)

set -e

# Konfiguration
SOURCE_DIR="/Users/albertgashi/Desktop/xyz/sesam"
BACKUP_BASE_DIR="/Users/albertgashi/Desktop/backups"
CLOUD_BACKUP_DIR="/Users/albertgashi/Documents/ParkSmart_Backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🌟 ParkSmart Erweiterte Backup-Strategie${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 1. Lokales Desktop Backup
echo -e "${YELLOW}📁 1. Lokales Desktop Backup...${NC}"
mkdir -p "$BACKUP_BASE_DIR"
DESKTOP_BACKUP="${BACKUP_BASE_DIR}/sesam_backup_${TIMESTAMP}"
cp -R "$SOURCE_DIR" "$DESKTOP_BACKUP"
echo -e "${GREEN}✅ Desktop Backup erstellt: $DESKTOP_BACKUP${NC}"

# 2. Documents Backup (für iCloud Sync)
echo -e "${YELLOW}☁️  2. Documents Backup (iCloud)...${NC}"
mkdir -p "$CLOUD_BACKUP_DIR"
CLOUD_BACKUP="${CLOUD_BACKUP_DIR}/sesam_backup_${TIMESTAMP}"
cp -R "$SOURCE_DIR" "$CLOUD_BACKUP"
echo -e "${GREEN}✅ Cloud Backup erstellt: $CLOUD_BACKUP${NC}"

# 3. Komprimierte Archive erstellen
echo -e "${YELLOW}🗜️  3. Erstelle komprimierte Archive...${NC}"
cd "$BACKUP_BASE_DIR"
tar -czf "sesam_backup_${TIMESTAMP}.tar.gz" "sesam_backup_${TIMESTAMP}"

cd "$CLOUD_BACKUP_DIR"
tar -czf "sesam_backup_${TIMESTAMP}.tar.gz" "sesam_backup_${TIMESTAMP}"
echo -e "${GREEN}✅ Komprimierte Archive erstellt${NC}"

# 4. Backup-Manifest erstellen
echo -e "${YELLOW}📋 4. Erstelle Backup-Manifest...${NC}"
cat > "$CLOUD_BACKUP_DIR/backup_manifest_${TIMESTAMP}.txt" << EOF
ParkSmart Backup Manifest
========================
Erstellt am: $(date)

Backup-Standorte:
1. Desktop: $DESKTOP_BACKUP
2. Documents: $CLOUD_BACKUP
3. Archive: $BACKUP_BASE_DIR/sesam_backup_${TIMESTAMP}.tar.gz
4. Cloud Archive: $CLOUD_BACKUP_DIR/sesam_backup_${TIMESTAMP}.tar.gz

Backup-Größen:
- Unkomprimiert: $(du -sh "$DESKTOP_BACKUP" | cut -f1)
- Komprimiert: $(du -sh "$BACKUP_BASE_DIR/sesam_backup_${TIMESTAMP}.tar.gz" | cut -f1)

Projekt-Status:
- Backend: FastAPI + MongoDB (Port 8000)
- Frontend: React + Tailwind (Port 3000)
- Interaktive Karte: React-Leaflet + OpenStreetMap
- Testbenutzer: 19 verfügbar
- Letzter Test: $(date)

Wiederherstellung:
1. Entpacke Archive: tar -xzf sesam_backup_${TIMESTAMP}.tar.gz
2. Backend: cd sesam/backend && uvicorn server:app --reload
3. Frontend: cd sesam/frontend && npm start
4. Login: user@test.com / password123

Wichtige Features:
✅ Benutzer-Authentifizierung (JWT)
✅ Admin-Dashboard
✅ Owner-Verwaltung  
✅ Interaktive Parkplatzkarte
✅ Payment-Integration (Stripe)
✅ Responsive Design
✅ MongoDB-Integration
✅ Map-Positioning-Fixes implementiert
EOF

echo -e "${GREEN}✅ Backup-Manifest erstellt${NC}"

# 5. Zusammenfassung
echo ""
echo -e "${BLUE}📊 Backup-Zusammenfassung${NC}"
echo -e "${BLUE}========================${NC}"
echo -e "✅ Desktop Backup: ${GREEN}$DESKTOP_BACKUP${NC}"
echo -e "✅ Cloud Backup: ${GREEN}$CLOUD_BACKUP${NC}"
echo -e "✅ Desktop Archiv: ${GREEN}$BACKUP_BASE_DIR/sesam_backup_${TIMESTAMP}.tar.gz${NC}"
echo -e "✅ Cloud Archiv: ${GREEN}$CLOUD_BACKUP_DIR/sesam_backup_${TIMESTAMP}.tar.gz${NC}"
echo ""
echo -e "${GREEN}🎉 Erfolgreich! 4 Backup-Kopien erstellt${NC}"
echo -e "${YELLOW}💡 Das Cloud-Backup wird automatisch mit iCloud synchronisiert${NC}"
echo ""
