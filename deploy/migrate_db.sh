#!/usr/bin/env bash
set -euo pipefail

# Run Python migration (simple create_all using SQLAlchemy models in backend/auth.py)
echo "Running DB migration (SQLAlchemy create_all)..."
python3 - <<'PY'
import auth
print('Using DATABASE_URL=', auth.DATABASE_URL)
auth.init_db()
print('DB migration complete')
PY

echo "Done"
