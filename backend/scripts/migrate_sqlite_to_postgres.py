"""Migrate users from SQLite to Postgres (idempotent)

This script migrates the `users` table from the local SQLite file to the
Postgres database referenced by the `DATABASE_URL` environment variable.
It is purposely conservative: it only migrates the `users` table, uses
email as the unique key, and performs upserts to avoid duplicates.

Run inside backend container where /app/backend/parking.db exists and
requirements (sqlalchemy, psycopg2) are available.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, select, insert, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

SQLITE_PATH = os.environ.get("SQLITE_PATH", "/app/backend/parking.db")
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(2)

print("SOURCE SQLITE:", SQLITE_PATH)
print("TARGET DB:", DATABASE_URL)

# Create engines
src_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
# ensure we use postgres dialect
tgt_engine = create_engine(DATABASE_URL)

src_meta = MetaData()
src_meta.reflect(bind=src_engine)

if 'users' not in src_meta.tables:
    print('No users table found in sqlite — nothing to migrate')
    sys.exit(0)

users_src = src_meta.tables['users']

# Ensure target users table exists (Alembic should have created it). Reflect target metadata.
tgt_meta = MetaData()
tgt_meta.reflect(bind=tgt_engine)

if 'users' not in tgt_meta.tables:
    print('Target users table does not exist — aborting. Run alembic upgrade head first')
    sys.exit(3)

users_tgt = tgt_meta.tables['users']

# Read rows from sqlite
with src_engine.connect() as s_conn:
    rows = s_conn.execute(select(users_src)).fetchall()

print(f"Found {len(rows)} rows in sqlite.users")

migrated = 0
skipped = 0

with tgt_engine.begin() as t_conn:
    for r in rows:
        # Build a dict of columns present in source row and match to target columns
        rowd = dict(r._mapping)
        # Normalize keys: ensure only keys that exist in target are used
        insert_data = {k: rowd.get(k) for k in users_tgt.c.keys() if k in rowd}
        # If id present, do not force id in inserts — prefer upsert by email
        if 'email' not in insert_data or not insert_data.get('email'):
            print('Skipping row without email:', rowd)
            skipped += 1
            continue

        stmt = pg_insert(users_tgt).values(**insert_data)
        # ON CONFLICT (email) DO UPDATE SET ... (update password_hash, role, last_login, name)
        do_update = {c.name: stmt.excluded[c.name] for c in users_tgt.c if c.name not in ('id','email','created_at')}
        stmt = stmt.on_conflict_do_update(index_elements=['email'], set_=do_update)
        try:
            t_conn.execute(stmt)
            migrated += 1
        except Exception as e:
            print('ERROR migrating', insert_data.get('email'), '->', e)

print(f"Migrated/Upserted: {migrated}, Skipped: {skipped}")
print('Done')
