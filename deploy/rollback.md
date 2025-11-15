# Rollback-Playbook

Kurzanleitung, um nach einem fehlgeschlagenen Deploy schnell auf die letzte stabile Version zurückzurollen.

## Voraussetzungen
- Zugriff per SSH auf den Server
- Der vorherige (stabile) Commit-SHA oder Image-Tag ist bekannt (z. B. über CI-Logs)

## Schritte

1) Optional: Status/Diagnose
```
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker logs --tail 200 parking_backend || true
curl -sS https://parking.gashis.ch/api/health | jq || true
```

2) Alte Images aufräumen (optional)
```
# Nur wenn Speicher knapp ist. Ansonsten überspringen.
docker image prune -f
```

3) Stabiles Tag setzen und deployen
```
# Beispiel: auf vorherigen Commit zurückrollen
export IMAGE_TAG=<STABILER_COMMIT_SHA>
./deploy/update.sh "$IMAGE_TAG"
```

4) Healthcheck prüfen
```
curl -sS https://parking.gashis.ch/api/health | jq
```

5) Falls weiterhin Probleme auftreten
- Backend-Logs prüfen:
```
docker logs --tail 300 parking_backend
```
- Proxy-Logs (falls relevant):
```
docker logs --tail 200 parking_proxy
```
- Datenbankverbindung (im Container):
```
docker exec -it parking_postgres psql -U ${POSTGRES_USER:-parking} -d ${POSTGRES_DB:-parkingdb} -c '\dt'
```

6) Post-Rollback Cleanup (optional)
- Nicht zwingend erforderlich; nach erfolgreichem Rollback kann man alte fehlerhafte Images entfernen.

## Hinweise
- `deploy/update.sh` sorgt für ein frisches `up -d --force-recreate` und prüft Health.
- Migrations: Bei Rollback werden keine Down-Migrationen ausgeführt. Bei inkompatibler DB-Struktur ggf. manuell handeln.
- Backups: Vor Deploys idealerweise `deploy/backup_db_fixed.sh` laufen lassen.
