# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import asyncio
import shutil
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

import sentry_sdk
import uvloop
from cashews.exceptions import CacheBackendInteractionError
from hydrogram import idle

from . import __version__, constants
from .client import AppParameters, Korone
from .config import ConfigManager
from .database.sqlite.connection import SQLite3Connection
from .modules.errors.utils import IGNORED_EXCEPTIONS
from .utils.caching import cache
from .utils.logging import logger


async def pre_process() -> ConfigManager:
    try:
        await cache.ping()
    except (CacheBackendInteractionError, TimeoutError):
        logger.critical("Can't connect to RedisDB! Exiting...")
        sys.exit(1)

    config = ConfigManager()

    if sentry_dsn := config.get("korone", "SENTRY_DSN"):
        await logger.ainfo("Initializing Sentry integration")
        sentry_sdk.init(
            dsn=sentry_dsn,
            release=__version__,
            ignore_errors=IGNORED_EXCEPTIONS,
        )

    async with SQLite3Connection() as conn:
        await conn.execute(constants.SQLITE3_TABLES, script=True)
        await conn.vacuum()

    return config


async def post_process() -> None:
    await cache.clear()

    with tempfile.TemporaryDirectory() as tmp_dir, suppress(FileNotFoundError):
        shutil.move(Path(constants.BOT_ROOT_PATH / "downloads").as_posix(), tmp_dir)


async def main() -> None:
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
