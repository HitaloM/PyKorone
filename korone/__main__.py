# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import platform
from datetime import datetime, timezone

import pyrogram
import pyromod
from pyrogram import Client, idle
from pyrogram.errors import BadRequest
from pyrogram.session import Session
from pyromod import listen
from pyromod.helpers import ikb
from rich import box
from rich import print as rprint
from rich.logging import RichHandler
from rich.panel import Panel

import korone
from korone.config import API_HASH, API_ID, SUDOERS, TOKEN
from korone.utils import filters, http, modules, shell_exec

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

client = Client(
    "client",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TOKEN,
    parse_mode="html",
    workers=24,
)

# Beautiful init with rich
text = ":rocket: [bold green]PyKorone Running...[/bold green] :rocket:"
text += f"\nKorone v{korone.__version__}"
text += f"\nPyrogram v{pyrogram.__version__}"
text += f"\n{korone.__license__}"
text += f"\n{korone.__copyright__}"
rprint(Panel.fit(text, border_style="blue", box=box.ASCII))


# Disable ugly pyrogram notice print
Session.notice_displayed = True


async def main():
    await client.start()

    # Save start time (useful for uptime info)
    client.start_time = datetime.now().replace(tzinfo=timezone.utc)

    # Monkeypatch
    client.me = await client.get_me()
    client.ikb = ikb

    # Built-in filters and modules load system
    filters.load(client)
    modules.load(client)

    # Saving commit number
    client.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])

    start_message = (
        f"<b>PyKorone <code>v{korone.__version__} "
        f"({client.version_code})</code> started...</b>\n"
        f"- <b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>\n"
        f"- <b>Pyromod:</b> <code>v{pyromod.__version__}</code>\n"
        f"- <b>Python:</b> <code>v{platform.python_version()}</code>\n"
        f"- <b>System:</b> <code>{client.system_version}</code>"
    )
    try:
        for user in SUDOERS:
            await client.send_message(chat_id=user, text=start_message)
    except BadRequest:
        log.warning("Unable to send the startup message to the SUDOERS")
        pass

    await idle()
    await http.aclose()
    await client.stop()
    log.info("PyKorone stopped... Bye!")


loop = asyncio.get_event_loop()

loop.run_until_complete(main())
