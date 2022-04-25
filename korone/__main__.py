# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import asyncio
import logging

from pyrogram import idle
from pyrogram.session import Session

from korone.database import database
from korone.korone import Korone, log
from korone.utils import http, is_windows

# Custom logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s.%(funcName)s | %(levelname)s | %(message)s",
    datefmt="[%X]",
)

# To avoid some annoying log
logging.getLogger("pyrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)


# Use uvloop to improve speed if available
try:
    import uvloop

    uvloop.install()
except ImportError:
    if not is_windows():
        log.warning("uvloop is not installed and therefore will be disabled.")


# Disable ugly pyrogram notice print
Session.notice_displayed = True


async def main() -> None:
    await database.connect()

    korone = Korone()
    await korone.start()
    await idle()
    await korone.stop()
    await http.aclose()

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
        log.warning("Forced stop... Bye!")
    finally:
        # close asyncio event loop
        event_loop.close()
