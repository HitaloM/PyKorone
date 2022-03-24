# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import asyncio
import logging

import aiohttp
import pyrogram
from pyrogram.session import Session
from rich import box
from rich import print as rprint
from rich.logging import RichHandler
from rich.panel import Panel

import korone
from korone.database import database
from korone.korone import Korone
from korone.utils import http, is_windows

# Logging colorized by rich
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)


# To avoid some pyrogram annoying log
logging.getLogger("pyrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)

log = logging.getLogger("rich")


# Use uvloop to improve speed if available
try:
    import uvloop

    uvloop.install()
except ImportError:
    if not is_windows():
        log.warning("uvloop is not installed and therefore will be disabled.")


# Beautiful init with rich
text = ":rocket: [bold green]PyKorone Running...[/bold green] :rocket:"
text += f"\nKorone v{korone.__version__}"
text += f"\nPyrogram v{pyrogram.__version__}"
text += f"\n{korone.__license__}"
text += f"\n{korone.__copyright__}"
rprint(Panel.fit(text, border_style="blue", box=box.ASCII))


# Disable ugly pyrogram notice print
Session.notice_displayed = True


async def close_http() -> None:
    # Closing the aiohttp session use by some packages.
    await aiohttp.ClientSession().close()

    # Closing the httpx session use by the bot.
    await http.aclose()


if __name__ == "__main__":
    # open new asyncio event loop
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    try:
        # start the bot
        event_loop.run_until_complete(database.connect())
        Korone().run()
    except KeyboardInterrupt:
        # exit gracefully
        log.warning("Forced stop... Bye!")
    finally:
        # close https connections and the DB if open
        event_loop.run_until_complete(close_http())
        if database.is_connected:
            event_loop.run_until_complete(database.close())
        # close asyncio event loop
        event_loop.close()
