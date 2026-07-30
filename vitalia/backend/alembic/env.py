"""Alembic env — vitalia backend (Story 11 T-be-1).

Vitalia has its own independent alembic chain (down_revision=None on first
migration). Follows Story 10 T-10 simplified pattern:
- Raw-SQL migrations (op.execute) — no SQLAlchemy autogenerate
- target_metadata=None — no model import required for upgrade/downgrade
- DB URL from POSTGRES_* env vars (matches vitalia src/core/config.py)

If autogenerate is needed in a future ticket, restore target_metadata via:
    from src.shared.domain.base_entity import Base
    # ... model imports ...
    target_metadata = Base.metadata
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Priorizar DATABASE_URL (SSoT canónica del compose). Convertir asyncpg→psycopg2
# porque alembic usa driver sync. Fallback a POSTGRES_* env vars para compat dev local sin Docker.
_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    # asyncpg → psycopg2 (alembic es sync)
    db_url = (
        _database_url
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )
else:
    db_url = (
        f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}"
        f":{os.environ.get('POSTGRES_PASSWORD', 'password')}"
        f"@{os.environ.get('POSTGRES_HOST', 'localhost')}"
        f":{os.environ.get('POSTGRES_PORT', '5432')}"
        f"/{os.environ.get('POSTGRES_DB', 'vitalia_dev')}"
    )
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Raw-SQL migrations use op.execute(); metadata not required for upgrade/downgrade.
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script generation)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (direct DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
