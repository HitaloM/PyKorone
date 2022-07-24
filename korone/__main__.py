# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import asyncio
import logging

from pyrogram import idle

from korone.bot import Korone
from korone.database import database

# Custom logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s.%(funcName)s | %(levelname)s | %(message)s",
    datefmt="[%X]",
)


logger = logging.getLogger(__name__)


# Use uvloop to improve speed
try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("uvloop is not installed and therefore will be disabled.")


async def main():
    await database.connect()

    korone = Korone()
    await korone.start()
    await idle()
    await korone.stop()

    if database.is_connected:
        await database.close()


if __name__ == "__main__":
    # open new asyncio event loop
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    try:
        # start the sqlite database and pyrogram client
        event_loop.run_until_complete(main())
    except KeyboardInterrupt:
        # exit gracefully
        logger.warning("Forced stop... Bye!")
    finally:
        # close asyncio event loop
        event_loop.close()
