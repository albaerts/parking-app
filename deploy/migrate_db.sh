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

# Ensure Postgres sequences are set correctly after migration to avoid PK collisions
echo "Resetting Postgres sequences (if applicable)..."
python3 - <<'PY'
import os
import sys
from urllib.parse import urlparse
try:
	from sqlalchemy import create_engine, text
except Exception as e:
	print('sqlalchemy not available, skipping sequence reset:', e)
	sys.exit(0)

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
	# try to import auth module which may expose DATABASE_URL
	try:
		import auth
		DATABASE_URL = getattr(auth, 'DATABASE_URL', None)
	except Exception:
		DATABASE_URL = None

if not DATABASE_URL:
	print('DATABASE_URL not set; cannot reset sequences')
	sys.exit(0)

engine = create_engine(DATABASE_URL)
tables = ['users', 'parking_spots', 'hardware_devices', 'hardware_commands']
with engine.begin() as conn:
	for t in tables:
		try:
			sql = f"SELECT setval(pg_get_serial_sequence('{t}','id'), COALESCE((SELECT MAX(id) FROM {t}), 1));"
			conn.execute(text(sql))
			print('Reset sequence for', t)
		except Exception as e:
			print('Warning: could not reset sequence for', t, '-', e)
print('Sequence reset complete')
PY

