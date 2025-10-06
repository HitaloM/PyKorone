# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import asyncio
import shutil
import sys
from contextlib import suppress
from pathlib import Path

import logfire
import uvloop
from cashews.exceptions import CacheBackendInteractionError
from hydrogram import idle

from . import __version__, constants
from .client import AppParameters, Korone
from .config import ConfigManager
from .database.sqlite.connection import SQLite3Connection
from .utils.caching import cache
from .utils.logging import configure_logging, logger


async def pre_process() -> ConfigManager:
    """Perform pre-startup tasks and configurations.

    Returns:
        The initialized ConfigManager instance

    Raises:
        SystemExit: If RedisDB connection fails
    """
    try:
        await cache.ping()
    except (CacheBackendInteractionError, TimeoutError):
        logger.critical("Can't connect to RedisDB! Exiting...")
        sys.exit(1)

    config = ConfigManager()

    await logger.ainfo("Configuring Logfire integration")
    logfire_token = (config.get("korone", "LOGFIRE_TOKEN") or "").strip() or None
    logfire_environment = (
        config.get("korone", "LOGFIRE_ENVIRONMENT", "production") or "production"
    ).strip()

    logfire_instance = logfire.configure(
        service_name="korone-bot",
        service_version=__version__,
        token=logfire_token,
        send_to_logfire="if-token-present",
        environment=logfire_environment,
    )
    configure_logging(logfire_instance=logfire_instance)
    logfire.instrument_httpx()

    async with SQLite3Connection() as conn:
        await conn.execute(constants.SQLITE3_TABLES, script=True)
        await conn.vacuum()

    return config


async def post_process() -> None:
    """Perform cleanup tasks after bot shutdown."""
    await cache.clear()

    downloads_path = Path(constants.BOT_ROOT_PATH / "downloads")
    with suppress(FileNotFoundError):
        shutil.rmtree(downloads_path, ignore_errors=True)


async def main() -> None:
    """Main function to start and manage the bot client."""
    config = await pre_process()

    params = AppParameters(
        api_id=config.get("hydrogram", "API_ID"),
        api_hash=config.get("hydrogram", "API_HASH"),
        bot_token=config.get("hydrogram", "BOT_TOKEN"),
    )

    client = Korone(params)

    try:
        await client.start()
        await idle()
    except Exception:
        await logger.aexception("An error occurred during client operation")
    finally:
        await client.stop()
        await post_process()


if __name__ == "__main__":
    try:
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    except KeyboardInterrupt:
        logger.warning("Forced stop... Bye!")
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=e)
        sys.exit(1)
