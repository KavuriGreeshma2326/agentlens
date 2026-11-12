"""Alembic environment script.

This file is executed by every ``alembic`` command.  It is responsible for:
1. Reading the DATABASE_URL from the environment (so the same migration can
   run in Docker, locally, or in CI without changing any file).
2. Importing all ORM models so that ``target_metadata`` contains every table
   (required for autogenerate to detect schema drift).
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ─── Path setup ──────────────────────────────────────────────────────────────
# Make ``app`` importable when running ``alembic`` from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Import models BEFORE Base.metadata is passed to Alembic ─────────────────
# If we skip this, Alembic won't see the tables and will generate empty diffs.
from app.database import Base  # noqa: E402
import app.models  # noqa: F401, E402  — registers all models with Base.metadata

# ─── Alembic Config ──────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    """Return the database URL from the environment, falling back to alembic.ini."""
    return os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")


def run_migrations_offline() -> None:
    """Run migrations without an active DB connection (useful for SQL dumps)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
