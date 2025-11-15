# Alembic Migrations

This directory contains the Alembic migration environment for the backend.

## Usage

Generate a new migration after modifying SQLAlchemy models (e.g. in `auth.py`):

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "add new field"
```

Apply migrations (upgrade to latest):

```bash
alembic -c backend/alembic.ini upgrade head
```

Downgrade (example one step):

```bash
alembic -c backend/alembic.ini downgrade -1
```

## Notes
- `env.py` pulls `DATABASE_URL` from the environment if set.
- Autogenerate compares against `auth.Base.metadata`.
- For SQLite autogenerate is limited; manual edits may be required for complex changes.
- The deploy script tries Alembic first and falls back to a lightweight create_all.
