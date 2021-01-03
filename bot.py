# This file is part of Korone (Telegram Bot)

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
import logging
from rich.logging import RichHandler
from rich import print, box
from rich.panel import Panel

from pyrogram import Client, idle

from config import API_ID, API_HASH, TOKEN

# Logging colorized by rich
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[
        RichHandler(
            rich_tracebacks=True)])

# To avoid some pyrogram annoying log
logging.getLogger("pyrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)

log = logging.getLogger("rich")

client = Client("bot", API_ID, API_HASH,
                bot_token=TOKEN,
                parse_mode="html",
                plugins=dict(root="handlers"))

# Beautiful init with rich
text = f":rocket: [bold green]PyKorone Running...[/bold green] :rocket:"
print(Panel.fit(text, border_style='blue', box=box.ASCII))

if __name__ == "__main__":
    client.start()
    idle()
