#!/bin/zsh
# Einfacher Wrapper für den End-to-End Smoke-Test
# Nutzung: ./run_smoke.sh
set -euo pipefail

# Optional: Projektverzeichnis bestimmen
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Falls virtualenv existiert, kann hier aktiviert werden
# Beispiel: source .venv-1/bin/activate  # optional

echo "🚀 Starte Smoke-Test (python3 smoke_e2e.py)"
python3 smoke_e2e.py
STATUS=$?

if [ $STATUS -eq 0 ]; then
  echo "✅ Smoke-Test erfolgreich"
else
  echo "❌ Smoke-Test fehlgeschlagen (Exit $STATUS)"
fi

exit $STATUS
