from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from alembic import command
from korone.config import CONFIG
from korone.db.engine import get_engine
from korone.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Connection

logger = get_logger(__name__)

LEGACY_BASELINE_REVISION = "1fc8a372560c"
BASELINE_TABLES = frozenset({"chats", "chat_topics", "disabled", "lang", "lastfm_users", "users_in_groups"})


def _project_root() -> Path:
    module_path = Path(__file__).resolve()

    # Prefer explicit deployment overrides when available.
    if configured_root := os.getenv("KORONE_PROJECT_ROOT"):
        return Path(configured_root).resolve()

    if configured_ini := os.getenv("KORONE_ALEMBIC_INI"):
        return Path(configured_ini).resolve().parent

    # Runtime often executes from project root (e.g. /app in Docker).
    cwd = Path.cwd().resolve()
    candidates = [cwd, *cwd.parents, *module_path.parents]

    for candidate in candidates:
        if (candidate / "alembic.ini").is_file() and (candidate / "alembic").is_dir():
            return candidate

    msg = "Could not locate Alembic project root. Set KORONE_PROJECT_ROOT or KORONE_ALEMBIC_INI in the environment."
    raise FileNotFoundError(msg)


def _create_alembic_config() -> AlembicConfig:
    root = _project_root()
    alembic_ini_path = root / "alembic.ini"
    alembic_dir_path = root / "alembic"

    if not alembic_ini_path.exists():
        msg = f"Alembic config not found: {alembic_ini_path}"
        raise FileNotFoundError(msg)
    if not alembic_dir_path.exists():
        msg = f"Alembic script directory not found: {alembic_dir_path}"
        raise FileNotFoundError(msg)

    config = AlembicConfig(str(alembic_ini_path))
    config.set_main_option("script_location", str(alembic_dir_path))
    config.set_main_option("sqlalchemy.url", CONFIG.db_url.replace("%", "%%"))
    return config


def _get_revision_state(connection: Connection, script: ScriptDirectory) -> tuple[set[str], set[str]]:
    context = MigrationContext.configure(connection)
    current_heads = set(context.get_current_heads())
    target_heads = set(script.get_heads())
    return current_heads, target_heads


def _get_existing_tables(connection: Connection) -> set[str]:
    return set(inspect(connection).get_table_names())


def _is_legacy_schema_without_alembic(current_heads: set[str], existing_tables: set[str]) -> bool:
    return not current_heads and "alembic_version" not in existing_tables and BASELINE_TABLES.issubset(existing_tables)


async def init_db() -> None:
    """Ensure database connectivity; schema changes are managed by Alembic."""
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def migrate_db_if_needed() -> bool:
    """Run Alembic migrations at startup only when DB revision is behind head."""
    alembic_config = _create_alembic_config()
    script = ScriptDirectory.from_config(alembic_config)
    engine = get_engine()
    has_changed = False

    async with engine.connect() as conn:
        current_heads, target_heads = await conn.run_sync(_get_revision_state, script)
        existing_tables = await conn.run_sync(_get_existing_tables)

    if _is_legacy_schema_without_alembic(current_heads, existing_tables):
        await logger.awarning(
            "Legacy schema detected without Alembic version; stamping baseline revision",
            baseline_revision=LEGACY_BASELINE_REVISION,
        )
        await asyncio.to_thread(command.stamp, alembic_config, LEGACY_BASELINE_REVISION)
        has_changed = True

        async with engine.connect() as conn:
            current_heads, target_heads = await conn.run_sync(_get_revision_state, script)

    if current_heads == target_heads:
        await logger.ainfo("Database schema already up to date", revision=sorted(target_heads))
        return has_changed

    await logger.ainfo(
        "Database schema outdated, running Alembic upgrade",
        current_revision=sorted(current_heads),
        target_revision=sorted(target_heads),
    )

    await asyncio.to_thread(command.upgrade, alembic_config, "head")
    has_changed = True

    async with engine.connect() as conn:
        current_heads_after, _ = await conn.run_sync(_get_revision_state, script)

    if current_heads_after != target_heads:
        msg = "Database migration finished with unexpected revision state"
        raise RuntimeError(msg)

    await logger.ainfo("Database migrations applied", revision=sorted(current_heads_after))
    return has_changed


async def close_db() -> None:
    engine = get_engine()
    await engine.dispose()
