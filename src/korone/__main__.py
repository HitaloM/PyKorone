# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import asyncio
import sys
from contextlib import suppress

import logfire
import uvloop
from anyio import Path
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

    config = await ConfigManager.create()

    await logger.ainfo("Configuring Logfire integration")
    logfire_token = config.get("korone", "LOGFIRE_TOKEN")
    logfire_environment = config.get("korone", "LOGFIRE_ENVIRONMENT")

    logfire_instance = logfire.configure(
        service_name="korone-bot",
        service_version=__version__,
        token=logfire_token,
        send_to_logfire="if-token-present",
        environment=logfire_environment,
    )
    logfire.instrument_httpx()
    configure_logging(logfire_instance=logfire_instance)

    async with SQLite3Connection() as conn:
        await conn.execute(constants.SQLITE3_TABLES, script=True)
        await conn.vacuum()

    return config


async def _remove_directory_tree(path: Path) -> None:
    if not await path.exists():
        return

    if not await path.is_dir():
        await path.unlink(missing_ok=True)
        return

    async for child in path.iterdir():
        if await child.is_dir():
            await _remove_directory_tree(child)
        else:
            await child.unlink(missing_ok=True)

    await path.rmdir()


async def post_process() -> None:
    """Perform cleanup tasks after bot shutdown."""
    await cache.clear()

    downloads_path = Path(str(constants.BOT_ROOT_PATH / "downloads"))
    with suppress(FileNotFoundError):
        await _remove_directory_tree(downloads_path)


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
