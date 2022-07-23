# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo

import datetime
import logging
from typing import List, Mapping, Union

import pytomlpp
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import BadRequest
from pyrogram.raw.all import layer
from pyrogram.types import User

from korone import __version__
from korone.utils import shell_exec

logger = logging.getLogger(__name__)

KoroneConfig = Mapping[str, Union[int, str, list]]


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        config_toml = pytomlpp.loads(open("config.toml", "r").read())
        self.pyrogram_config: KoroneConfig = config_toml["pyrogram"]
        self.korone_config: KoroneConfig = config_toml["korone"]

        # Pyrogram specif configs
        api_id = self.pyrogram_config["api_id"]
        if not isinstance(api_id, int):
            raise TypeError("API ID must be an integer")

        api_hash = self.pyrogram_config["api_hash"]
        if not isinstance(api_hash, str):
            raise TypeError("API hash must be a string")

        bot_token = self.pyrogram_config["bot_token"]
        if not isinstance(bot_token, str):
            raise TypeError("Bot token must be a string")

        workers = self.pyrogram_config["workers"]
        if not isinstance(workers, int):
            raise TypeError("Workers must be an integer")

        excluded_plugins = self.pyrogram_config["excluded_plugins"]
        if not isinstance(excluded_plugins, list):
            raise TypeError("Excluded plugins must be a list of strings")

        # Korone specific configs
        sudoers = self.korone_config["sudoers"]
        if not isinstance(sudoers, list):
            raise TypeError("Sudoers must be a list of integers")

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
