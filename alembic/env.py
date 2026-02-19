from __future__ import annotations

import asyncio
import os
import sys
import types
from logging.config import fileConfig
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _bootstrap_korone_namespace() -> None:
    if "korone" in sys.modules:
        return

    korone_module = types.ModuleType("korone")
    korone_module.__path__ = [str(SRC_DIR / "korone")]
    sys.modules["korone"] = korone_module


_bootstrap_korone_namespace()

from korone.db import models as _models  # noqa: E402, F401
from korone.db.base import Base  # noqa: E402

if TYPE_CHECKING:
    from sqlalchemy import Connection

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _db_url_from_env_file() -> str | None:
    env_path = ROOT_DIR / "data" / "config.env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        if separator and key.strip() == "DB_URL":
            return value.strip().strip("'\"")

    return None


def _database_url() -> str:
    return os.getenv("DB_URL") or _db_url_from_env_file() or config.get_main_option("sqlalchemy.url")  # pyright: ignore[reportReturnType]


config.set_main_option("sqlalchemy.url", _database_url().replace("%", "%%"))


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_sync_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True, compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_run_sync_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
