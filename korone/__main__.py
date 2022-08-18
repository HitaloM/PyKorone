# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import asyncio

from pyrogram import idle

from .bot import Korone
from .database import database
from .utils.logger import log

try:
    import uvloop

    uvloop.install()
except ImportError:
    log.warning("uvloop is not installed and therefore will be disabled.")


async def main():
    await database.connect()

    korone = Korone()
    await korone.start()
    await idle()
    await korone.stop()

    if database.is_connected:
        await database.close()


if __name__ == "__main__":
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    try:
        event_loop.run_until_complete(main())
    except KeyboardInterrupt:
        log.warning("Forced stop... Bye!")
    finally:
        event_loop.close()
