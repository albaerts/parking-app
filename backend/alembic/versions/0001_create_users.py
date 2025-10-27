"""create users table

Revision ID: 0001_create_users
Revises: 
Create Date: 2025-10-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_create_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    # If users table does not exist, create it. If it exists, add missing columns.
    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('email', sa.String(length=255), nullable=False, unique=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=50), nullable=True, server_default='user'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('last_login', sa.DateTime(), nullable=True),
        )
    else:
        # Check existing columns and add missing ones
        res = bind.execute(sa.text("PRAGMA table_info('users')")).fetchall()
        existing_cols = [r[1] for r in res]
        if 'password_hash' not in existing_cols:
            op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
        if 'role' not in existing_cols:
            op.add_column('users', sa.Column('role', sa.String(length=50), nullable=True, server_default='user'))
        if 'last_login' not in existing_cols:
            op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))


def downgrade():
    # Downgrade: remove columns if present, or drop table if it was created by this migration
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'users' in insp.get_table_names():
        # Attempt to drop added columns where supported; SQLite doesn't support DROP COLUMN easily,
        # so for safety we do not attempt catastrophic schema changes here.
        pass
