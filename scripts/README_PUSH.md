# Anleitung: Repo auf GitHub hochladen

Dieses Skript hilft dir, das lokale Projekt auf GitHub zu veröffentlichen. Es unterstützt die GitHub CLI (`gh`) zum automatischen Anlegen eines Repositories oder das Setzen einer Remote-URL.

Schnellstart (empfohlen):

1. Installiere Git und (optional) die GitHub CLI `gh`:
   - macOS: `brew install git gh`

2. Prüfe das Skript mit Dry-Run:

```bash
./scripts/push_to_github.sh --dry-run
```

3a. Wenn du die `gh` CLI verwendest und ein neues Repo anlegen willst:

```bash
# Beispiel: gh Repo im Account 'myuser' oder Org 'myorg'
./scripts/push_to_github.sh --create myuser/myrepo --public
```

3b. Alternativ: Erstelle das Repo über die GitHub Website und verwende die Remote-URL:

```bash
./scripts/push_to_github.sh --remote https://github.com/you/yourrepo.git
# danach
chmod +x scripts/push_to_github.sh
./scripts/push_to_github.sh --remote https://github.com/you/yourrepo.git
```

Hinweise & Security:
- Das Skript ignoriert nicht automatisch sensible Dateien. Wir haben eine `.gitignore` angelegt, die u.a. `backend/parking.db` ausschließt.
- Wenn du SSH-URLs verwenden willst, stelle sicher, dass dein SSH-Key bei GitHub hinterlegt ist.
- Für CI/CD: Füge deine Docker-Registry-Zugangsdaten und SSH-Keys als Secrets in GitHub ein.

Wenn du möchtest, kann ich den Push hier automatisch für dich ausführen — dafür musst du mir entweder die Remote-URL mitteilen (ich kann nicht mit deinen Credentials interagieren) oder du führst die obigen Befehle lokal aus. Wenn du willst, helfe ich dir beim Erstellen eines Repos per `gh` (ich kann die passenden Befehle hier vorbereiten).
