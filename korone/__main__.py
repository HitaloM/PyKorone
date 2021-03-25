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

import os
import sys

# Clean Terminal
os.system("clear")

# Update requirements
DGRAY = 'echo -e "\033[1;30m"'
RESET = 'echo -e "\033[0m"'

if "--no-update" not in sys.argv:
    print("\033[0;32mUpdating requirements...\033[0m")
    os.system(f"{DGRAY}; {sys.executable} -m pip install . -U; {RESET}")
    os.system("clear")

print("\033[0m")
os.system("clear")

import re
import logging
import platform
from tortoise import run_async
from rich import box, print
from rich.logging import RichHandler
from rich.panel import Panel

import pyromod
import pyrogram
from pyromod import filters
from pyromod.helpers import ikb
from pyrogram import Client, filters, idle
from pyrogram.session import Session

import korone
from korone.utils import http
from korone.database import connect_database
from korone.config import API_HASH, API_ID, SUDOERS, TOKEN, prefix
from korone.handlers import COMMANDS_HELP

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
    API_ID,
    API_HASH,
    bot_token=TOKEN,
    parse_mode="html",
    plugins=dict(root="korone/handlers"),
)

# Beautiful init with rich
text = ":rocket: [bold green]PyKorone Running...[/bold green] :rocket:"
text += f"\nKorone v{korone.__version__}"
text += f"\nPyrogram v{pyrogram.__version__}"
text += f"\n{korone.__license__}"
text += f"\n{korone.__copyright__}"
print(Panel.fit(text, border_style="blue", box=box.ASCII))


# monkeypatch
def int_filter(filter, group: str = "others", action: str = None, *args, **kwargs):
    COMMANDS_HELP[group]["filters"][filter] = {"action": action or " "}
    return filters.regex(r"(?i)^{0}(\.|\?|\!)?$".format(filter), *args, **kwargs)


def command_filter(
    command, group: str = "general", action: str = None, *args, **kwargs
):
    if command not in COMMANDS_HELP[group]["commands"].keys():
        COMMANDS_HELP[group]["commands"][command] = {"action": action or ""}
    prefixes = "".join(prefix)
    _prefix = f"^[{re.escape(prefixes)}]"
    return filters.regex(_prefix + command, *args, **kwargs)


pyrogram.filters.cmd = command_filter
pyrogram.filters.int = int_filter


# Disable ugly pyrogram notice print
Session.notice_displayed = True


# Init client
async def main():
    await connect_database()

    await client.start()
    client.me = await client.get_me()
    client.ikb = ikb

    start_message = f"""<b>PyKorone <code>v{korone.__version__}</code> started...</b>
- <b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>
- <b>Pyromod:</b> <code>v{pyromod.__version__}</code>
- <b>Python:</b> <code>v{platform.python_version()}</code>
- <b>System:</b> <code>{client.system_version}</code>
           """
    try:
        for user in SUDOERS:
            await client.send_message(chat_id=user, text=start_message)
    except BaseException:
        pass

    await idle()
    await http.aclose()


if __name__ == "__main__":
    run_async(main())
