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

import logging
import platform
import sys
from datetime import datetime, timezone

import pyrogram
from pyrogram import Client
from pyrogram.errors import BadRequest
from pyrogram.helpers import ikb
from pyrogram.raw.all import layer
from pyrogram.types import Message, User

import korone
from korone.config import API_HASH, API_ID, SUDOERS, TOKEN
from korone.utils import filters, http, modules, shell_exec

log = logging.getLogger(__name__)


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            session_name=name,
            app_version=f"PyKorone v{korone.__version__}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=TOKEN,
            parse_mode="html",
            workers=24,
            sleep_threshold=180,
        )

        # Save start time (useful for uptime info)
        self.start_time = datetime.now().replace(tzinfo=timezone.utc)

    async def start(self):
        await super().start()

        # Saving commit number
        self.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])

        # Misc monkeypatch
        self.me = await self.get_me()
        self.is_sudo = SUDOERS
        self.ikb = ikb

        log.info(
            "PyKorone for Pyrogram v%s (Layer %s) started on @%s. Hi.",
            pyrogram.__version__,
            layer,
            self.me.username,
        )

        # Built-in modules and filters system
        filters.load(self)
        modules.load(self)

        # Startup message
        start_message = (
            f"<b>PyKorone <code>v{korone.__version__} "
            f"({self.version_code})</code> started...</b>\n"
            f"- <b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>\n"
            f"- <b>Python:</b> <code>v{platform.python_version()}</code>\n"
            f"- <b>System:</b> <code>{self.system_version}</code>"
        )
        try:
            for user in self.is_sudo:
                await self.send_message(chat_id=user, text=start_message)
        except BadRequest:
            log.warning("Unable to send the startup message to the SUDOERS")

    async def stop(self, *args):
        await http.aclose()  # Closing the httpx session
        await super().stop()
        log.info("PyKorone stopped... Bye.")
        sys.exit()

    async def int_reply(self, m: Message, text: str = None):
        if m.chat.type == "private":
            await m.reply_text(text)
        elif m.reply_to_message and m.reply_to_message.from_user.id == self.me.id:
            await m.reply_text(text)
            return

    def is_sudoer(self, user: User) -> bool:
        return user.id in self.is_sudo
