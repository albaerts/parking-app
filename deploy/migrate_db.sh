#!/usr/bin/env bash
set -euo pipefail

# Prefer Alembic migrations when available; fallback to SQLAlchemy create_all
set +e
if python3 -m alembic --help >/dev/null 2>&1 || command -v alembic >/dev/null 2>&1; then
	echo "Running Alembic migrations (upgrade head)..."
	python3 -m alembic -c backend/alembic.ini upgrade head
	EXIT_CODE=$?
	if [ $EXIT_CODE -eq 0 ]; then
		echo "Alembic migrations applied successfully."
		exit 0
	else
		echo "Alembic migration failed with exit code $EXIT_CODE, falling back to create_all"
	fi
fi
set -e

echo "Running DB migration (SQLAlchemy create_all)..."
python3 - <<'PY'
import auth
print('Using DATABASE_URL=', auth.DATABASE_URL)
auth.init_db()
print('DB migration complete')
PY

echo "Done"
