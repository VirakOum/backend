from __future__ import annotations

import importlib
from logging.config import fileConfig
import os
import pkgutil
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app

from app.db import Base
from app.config import DATABASE_URL

# Import all app model modules so Base.metadata includes generated models.
for module in pkgutil.iter_modules(app.__path__):
    if module.name == "models" or module.name.startswith("models_"):
        importlib.import_module(f"app.{module.name}")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", DATABASE_URL))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_num_length=128,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        from sqlalchemy import text
        connection.execute(
            text("ALTER TABLE IF EXISTS alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);")
        )
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_num_length=128,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
