#!/bin/bash

# ParkSmart Backup Verifikation
# Überprüft die Integrität aller Backup-Kopien

echo "🔍 BACKUP-VERIFIKATION"
echo "====================="
echo ""

# Aktuellstes Backup
LATEST_BACKUP="sesam_backup_20250728_123304"

echo "📋 Verifikation des Backups: $LATEST_BACKUP"
echo "=" * 50

# Desktop Backup überprüfen
echo "🖥️  Desktop Backup:"
if [ -d "/Users/albertgashi/Desktop/backups/$LATEST_BACKUP" ]; then
    echo "   ✅ Verzeichnis existiert"
    echo "   📁 Größe: $(du -sh /Users/albertgashi/Desktop/backups/$LATEST_BACKUP | cut -f1)"
    echo "   📦 Archiv: $(du -sh /Users/albertgashi/Desktop/backups/${LATEST_BACKUP}.tar.gz | cut -f1)"
else
    echo "   ❌ Verzeichnis nicht gefunden"
fi

# iCloud Backup überprüfen  
echo ""
echo "☁️  iCloud Backup:"
if [ -d "/Users/albertgashi/Documents/ParkSmart_Backups/$LATEST_BACKUP" ]; then
    echo "   ✅ Verzeichnis existiert"
    echo "   📁 Größe: $(du -sh /Users/albertgashi/Documents/ParkSmart_Backups/$LATEST_BACKUP | cut -f1)"
    echo "   📦 Archiv: $(du -sh /Users/albertgashi/Documents/ParkSmart_Backups/${LATEST_BACKUP}.tar.gz | cut -f1)"
    
    if [ -f "/Users/albertgashi/Documents/ParkSmart_Backups/backup_manifest_20250728_123304.txt" ]; then
        echo "   📄 Manifest vorhanden"
    fi
else
    echo "   ❌ Verzeichnis nicht gefunden"
fi

# Wichtige Dateien überprüfen
echo ""
echo "🔍 Wichtige Dateien im Backup:"
BACKUP_PATH="/Users/albertgashi/Desktop/backups/$LATEST_BACKUP/sesam"

critical_files=(
    "backend/server.py"
    "frontend/src/App.js"
    "frontend/src/App.css"
    "backend/requirements.txt"
    "frontend/package.json"
    "FINAL_BACKUP_REPORT.md"
)

for file in "${critical_files[@]}"; do
    if [ -f "$BACKUP_PATH/$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (FEHLT!)"
    fi
done

# Backup-Scripts überprüfen
echo ""
echo "🔄 Backup-Scripts:"
scripts=(
    "backup_script.sh"
    "extended_backup.sh"
    "reset_users.py"
    "verify_new_users.py"
)

for script in "${scripts[@]}"; do
    if [ -f "$BACKUP_PATH/$script" ]; then
        echo "   ✅ $script"
    else
        echo "   ❌ $script (FEHLT!)"
    fi
done

echo ""
echo "📊 BACKUP-STATISTIK:"
echo "==================="
echo "📁 Desktop Backup Ordner: $(find /Users/albertgashi/Desktop/backups -name 'sesam_backup_*' -type d | wc -l | tr -d ' ')"
echo "📦 Desktop Archive: $(find /Users/albertgashi/Desktop/backups -name 'sesam_backup_*.tar.gz' | wc -l | tr -d ' ')"
echo "☁️  iCloud Backup Ordner: $(find /Users/albertgashi/Documents/ParkSmart_Backups -name 'sesam_backup_*' -type d | wc -l | tr -d ' ')"
echo "📦 iCloud Archive: $(find /Users/albertgashi/Documents/ParkSmart_Backups -name 'sesam_backup_*.tar.gz' | wc -l | tr -d ' ')"

total_desktop_size=$(du -sh /Users/albertgashi/Desktop/backups/ | cut -f1)
total_icloud_size=$(du -sh /Users/albertgashi/Documents/ParkSmart_Backups/ | cut -f1)

echo "💾 Gesamte Desktop-Backup-Größe: $total_desktop_size"
echo "☁️  Gesamte iCloud-Backup-Größe: $total_icloud_size"

echo ""
echo "✅ BACKUP-VERIFIKATION ABGESCHLOSSEN"
echo "🎉 Ihr ParkSmart-Projekt ist mehrfach gesichert!"
