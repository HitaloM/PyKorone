# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

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

from korone import __version__, app_dir, cache
from korone.client import AppParameters, Korone
from korone.config import ConfigManager
from korone.utils.logging import logger


async def main() -> None:
    try:
        await cache.ping()
    except (CacheBackendInteractionError, TimeoutError):
        logger.critical("Can't connect to RedisDB! Exiting...")
        sys.exit(1)

    config = ConfigManager()

    if sentry_dsn := config.get("korone", "SENTRY_DSN"):
        logger.info("Initializing Sentry integration")
        sentry_sdk.init(dsn=sentry_dsn, release=__version__)

    params = AppParameters(
        api_id=config.get("hydrogram", "API_ID"),
        api_hash=config.get("hydrogram", "API_HASH"),
        bot_token=config.get("hydrogram", "BOT_TOKEN"),
    )

    client = Korone(params)

    await client.start()
    await idle()

    with tempfile.TemporaryDirectory() as tmp_dir:
        for path in ("tmp", "downloads"):
            with suppress(FileNotFoundError):
                shutil.move(Path(app_dir / path).as_posix(), tmp_dir)

    await client.stop()


if __name__ == "__main__":
    try:
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    except KeyboardInterrupt:
        logger.warning("Forced stop... Bye!")
