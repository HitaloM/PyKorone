# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import sys

import uvloop
from cashews.exceptions import CacheBackendInteractionError
from hydrogram import idle

from korone import cache
from korone.client import AppParameters, Korone
from korone.config import ConfigManager
from korone.utils.logging import log


async def main() -> None:
    try:
        await cache.ping()
    except (CacheBackendInteractionError, TimeoutError):
        log.critical("Can't connect to RedisDB! Exiting...")
        sys.exit(1)

    config = ConfigManager()

    params = AppParameters(
        api_id=config.get("hydrogram", "API_ID"),
        api_hash=config.get("hydrogram", "API_HASH"),
        bot_token=config.get("hydrogram", "BOT_TOKEN"),
    )

    client = Korone(params)

    await client.start()
    await idle()
    await client.stop()


if __name__ == "__main__":
    try:
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    except KeyboardInterrupt:
        log.warning("Forced stop... Bye!")
