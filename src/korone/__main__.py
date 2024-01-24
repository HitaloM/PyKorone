# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import asyncio

import uvloop
from hydrogram import idle

from korone.client import AppParameters, Korone
from korone.config import ConfigManager
from korone.utils.logging import log

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def main() -> None:
    """
    Main entry point of the program.

    This function initializes the configuration, creates an instance of the Korone class,
    starts the client, waits for it to become idle, and then stops the client.
    """
    config = ConfigManager()

    config.init()

    params: AppParameters = AppParameters(
        api_id=config.get("hydrogram", "API_ID"),
        api_hash=config.get("hydrogram", "API_HASH"),
        bot_token=config.get("hydrogram", "BOT_TOKEN"),
    )

    client = Korone(params)
    await client.start()
    await idle()
    await client.stop()


if __name__ == "__main__":
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    try:
        event_loop.run_until_complete(main())
    except KeyboardInterrupt:
        log.warning("Forced stop... Bye!")
    finally:
        event_loop.close()
