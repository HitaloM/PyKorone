# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import datetime
import logging

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import BadRequest
from pyrogram.raw.all import layer
from pyrogram.types import User

from korone import __version__
from korone.config import config
from korone.utils import load_modules, shell_exec

logger = logging.getLogger(__name__)


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name=name,
            app_version=f"Korone v{__version__}",
            api_id=config.get_config("api_id", "pyrogram"),
            api_hash=config.get_config("api_hash", "pyrogram"),
            bot_token=config.get_config("bot_token", "pyrogram"),
            parse_mode=ParseMode.HTML,
            workers=config.get_config("workers", "pyrogram"),
            workdir="korone",
            sleep_threshold=180,
        )

        # Sudoers list
        self.sudoers = config.get_config("sudoers")

        # Bot startup time
        self.start_datetime = datetime.datetime.now().replace(
            tzinfo=datetime.timezone.utc
        )

    async def start(self):
        await super().start()
        load_modules(self)

        # Save version info
        self.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])
        self.version = str((await shell_exec("git rev-parse --short HEAD"))[0])

        self.me = await self.get_me()
        logger.info(
            "[%s] Running with Pyrogram v%s (Layer %s) started on @%s. Hi!",
            self.name,
            __version__,
            layer,
            self.me.username,
        )

        try:
            for sudo in self.sudoers:
                await self.send_message(
                    chat_id=sudo,
                    text=(
                        f"<b>Korone</b> <a href='https://github.com/AmanoTeam/PyKorone/commit/{self.version}'>{self.version}</a>"
                        f" (<code>{self.version_code}</code>) started! \n<b>Pyrogram</b> <code>v{__version__}</code> (Layer {layer})"
                    ),
                    disable_web_page_preview=True,
                )
        except BadRequest:
            logger.error(
                "[%s] Error while sending the startup message.",
                self.name,
                exc_info=True,
            )

    async def stop(self):
        await super().stop()
        logger.warning("[%s] Stopped. Bye!", self.name)

    def is_sudo(self, user: User) -> bool:
        return user.id in self.sudoers
