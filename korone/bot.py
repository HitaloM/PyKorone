# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo

import datetime
import logging

import pytomlpp
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import BadRequest
from pyrogram.raw.all import layer
from pyrogram.types import User

from korone import __version__
from korone.utils import shell_exec

logger = logging.getLogger(__name__)


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        config_toml = pytomlpp.loads(open("config.toml", "r").read())

        # Pyrogram specif configs
        api_id = config_toml["pyrogram"]["api_id"]
        api_hash = config_toml["pyrogram"]["api_hash"]
        bot_token = config_toml["pyrogram"]["bot_token"]
        workers = config_toml["pyrogram"]["workers"]
        excluded_plugins = config_toml["pyrogram"]["excluded_plugins"]

        # Korone specific configs
        sudoers = config_toml["korone"]["sudoers"]

        super().__init__(
            name=name,
            app_version=f"Korone v{__version__}",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            parse_mode=ParseMode.HTML,
            workers=workers,
            plugins=dict(root="korone.modules", exclude=excluded_plugins),
            workdir="korone",
            sleep_threshold=180,
        )

        # Sudoers list
        self.sudoers = sudoers

        # Bot startup time
        self.start_datetime = datetime.datetime.now().replace(
            tzinfo=datetime.timezone.utc
        )

    async def start(self):
        await super().start()

        # Save version info
        self.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])
        self.version = str((await shell_exec("git rev-parse --short HEAD"))[0])

        self.me = await self.get_me()
        logger.info(
            "Korone running with Pyrogram v%s (Layer %s) started on @%s. Hi!",
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
            logger.error("Error while sending the startup message.", exc_info=True)

    async def stop(self):
        await super().stop()
        logger.warning("Korone stopped. Bye!")

    def is_sudo(self, user: User) -> bool:
        return user.id in self.sudoers
