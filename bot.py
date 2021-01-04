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

import logging
import platform

import pyrogram
import pyromod.listen
from pyrogram import Client, idle
from pyrogram.errors.exceptions.bad_request_400 import BadRequest
from rich import box, print
from rich.logging import RichHandler
from rich.panel import Panel

from config import API_HASH, API_ID, OWNER, TOKEN

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
    "bot",
    API_ID,
    API_HASH,
    bot_token=TOKEN,
    parse_mode="html",
    plugins=dict(root="handlers"),
)

# Beautiful init with rich
text = ":rocket: [bold green]PyKorone Running...[/bold green] :rocket:"
print(Panel.fit(text, border_style="blue", box=box.ASCII))

with client:
    if __name__ == "__main__":
        try:
            client.send_message(
                OWNER,
                f"""<b>PyKorone Started...</b>
- <b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>
- <b>Pyromod:</b> <code>v{pyromod.__version__}</code>
- <b>Python:</b> <code>v{platform.python_version()}</code>
- <b>System:</b> <code>{client.system_version}</code>
           """,
            )
        except BadRequest:
            logging.warning("Cannot send startup message to SUDOERS...")
        idle()
