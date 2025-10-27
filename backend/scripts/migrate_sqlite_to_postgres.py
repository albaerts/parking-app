#!/usr/bin/env python3
"""
Safe migration script copying selected tables from the local SQLite file to Postgres.
Runs inside the backend container where requirements are installed.

Usage (inside container):
  python3 backend/scripts/migrate_sqlite_to_postgres.py

It reads DATABASE_URL from env and uses /app/backend/parking.db as SQLite source.
It performs idempotent upserts (ON CONFLICT DO NOTHING) for tables with unique keys.
"""
import os
import sqlite3
from urllib.parse import urlparse
import sqlalchemy as sa
from sqlalchemy import text

SQLITE_PATH = '/app/backend/parking.db'
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise SystemExit('DATABASE_URL is not set')

engine = sa.create_engine(DATABASE_URL)

def copy_users(conn_sqlite, pg_conn):
    cur = conn_sqlite.cursor()
    cur.execute('SELECT id, email, name, password_hash, role, created_at, last_login FROM users')
    rows = cur.fetchall()
    inserted = 0
    for r in rows:
        id_, email, name, password_hash, role, created_at, last_login = r
        # Upsert by email
        stmt = text(
            """
            INSERT INTO users (id, email, name, password_hash, role, created_at, last_login)
            VALUES (:id, :email, :name, :password_hash, :role, :created_at, :last_login)
            ON CONFLICT (email) DO UPDATE SET
              name = EXCLUDED.name,
              password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash),
              role = COALESCE(EXCLUDED.role, users.role),
              last_login = COALESCE(EXCLUDED.last_login, users.last_login)
            """
        )
        pg_conn.execute(stmt, dict(id=id_, email=email, name=name, password_hash=password_hash, role=role, created_at=created_at, last_login=last_login))
        inserted += 1
    return inserted

def copy_parking_spots(conn_sqlite, pg_conn):
    cur = conn_sqlite.cursor()
    cur.execute('SELECT id, name, address, latitude, longitude, status, price_per_hour, created_at FROM parking_spots')
    rows = cur.fetchall()
    inserted = 0
    for r in rows:
        id_, name, address, lat, lon, status, price, created_at = r
        stmt = text(
            """
            INSERT INTO parking_spots (id, name, address, latitude, longitude, status, price_per_hour, created_at)
            VALUES (:id, :name, :address, :latitude, :longitude, :status, :price_per_hour, :created_at)
            ON CONFLICT (id) DO NOTHING
            """
        )
        pg_conn.execute(stmt, dict(id=id_, name=name, address=address, latitude=lat, longitude=lon, status=status, price_per_hour=price, created_at=created_at))
        inserted += 1
    return inserted

def copy_hardware_devices(conn_sqlite, pg_conn):
    cur = conn_sqlite.cursor()
    cur.execute('SELECT id, hardware_id, owner_email, parking_spot_id, created_at FROM hardware_devices')
    rows = cur.fetchall()
    inserted = 0
    for r in rows:
        id_, hardware_id, owner_email, parking_spot_id, created_at = r
        stmt = text(
            """
            INSERT INTO hardware_devices (id, hardware_id, owner_email, parking_spot_id, created_at)
            VALUES (:id, :hardware_id, :owner_email, :parking_spot_id, :created_at)
            ON CONFLICT (hardware_id) DO UPDATE SET
              owner_email = COALESCE(EXCLUDED.owner_email, hardware_devices.owner_email),
              parking_spot_id = COALESCE(EXCLUDED.parking_spot_id, hardware_devices.parking_spot_id)
            """
        )
        pg_conn.execute(stmt, dict(id=id_, hardware_id=hardware_id, owner_email=owner_email, parking_spot_id=parking_spot_id, created_at=created_at))
        inserted += 1
    return inserted

def copy_hardware_commands(conn_sqlite, pg_conn):
    cur = conn_sqlite.cursor()
    cur.execute('SELECT id, hardware_id, command, parameters, status, issued_by, created_at, claimed_at, executed_at FROM hardware_commands')
    rows = cur.fetchall()
    inserted = 0
    for r in rows:
        id_, hardware_id, command, parameters, status, issued_by, created_at, claimed_at, executed_at = r
        stmt = text(
            """
            INSERT INTO hardware_commands (id, hardware_id, command, parameters, status, issued_by, created_at, claimed_at, executed_at)
            VALUES (:id, :hardware_id, :command, :parameters, :status, :issued_by, :created_at, :claimed_at, :executed_at)
            ON CONFLICT (id) DO NOTHING
            """
        )
        pg_conn.execute(stmt, dict(id=id_, hardware_id=hardware_id, command=command, parameters=parameters, status=status, issued_by=issued_by, created_at=created_at, claimed_at=claimed_at, executed_at=executed_at))
        inserted += 1
    return inserted

def main():
    if not os.path.exists(SQLITE_PATH):
        print('SQLite source not found at', SQLITE_PATH)
        return
    print('Connecting to SQLite:', SQLITE_PATH)
    conn_sqlite = sqlite3.connect(SQLITE_PATH)

    print('Connecting to Postgres via', DATABASE_URL)
    with engine.begin() as pg_conn:
        # Ensure target tables exist (idempotent). Alembic may have created users but other tables
        # (parking_spots, hardware_devices, hardware_commands) could be missing; create them here if needed.
        pg_conn.execute(text('''
            CREATE TABLE IF NOT EXISTS parking_spots (
                id INTEGER PRIMARY KEY,
                name TEXT,
                address TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                status TEXT,
                price_per_hour NUMERIC,
                created_at TIMESTAMP
            )
        '''))
        pg_conn.execute(text('''
            CREATE TABLE IF NOT EXISTS hardware_devices (
                id INTEGER PRIMARY KEY,
                hardware_id TEXT UNIQUE,
                owner_email TEXT,
                parking_spot_id INTEGER,
                created_at TIMESTAMP
            )
        '''))
        pg_conn.execute(text('''
            CREATE TABLE IF NOT EXISTS hardware_commands (
                id INTEGER PRIMARY KEY,
                hardware_id TEXT NOT NULL,
                command TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'queued',
                issued_by TEXT,
                created_at TIMESTAMP,
                claimed_at TIMESTAMP,
                executed_at TIMESTAMP
            )
        '''))

        print('Ensured target tables exist')

        print('Copying users...')
        u = copy_users(conn_sqlite, pg_conn)
        print('Copied users:', u)
        print('Copying parking_spots...')
        p = copy_parking_spots(conn_sqlite, pg_conn)
        print('Copied parking_spots:', p)
        print('Copying hardware_devices...')
        h = copy_hardware_devices(conn_sqlite, pg_conn)
        print('Copied hardware_devices:', h)
        print('Copying hardware_commands...')
        c = copy_hardware_commands(conn_sqlite, pg_conn)
        print('Copied hardware_commands:', c)

    conn_sqlite.close()
    print('Migration complete')

if __name__ == '__main__':
    main()
