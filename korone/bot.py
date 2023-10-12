# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import datetime

import aiocron
import pyrogram
import sentry_sdk
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import BadRequest
from pyrogram.raw.all import layer
from pyrogram.types import User

from . import __version__
from .config import config
from .utils import backup
from .utils.logger import log
from .utils.modules import load_modules
from .utils.system import shell_exec


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name=name,
            app_version=f"Korone v{__version__}",
            api_id=config.get_config("api_id", "pyrogram"),
            api_hash=config.get_config("api_hash", "pyrogram"),
            bot_token=config.get_config("bot_token", "pyrogram"),
            ipv6=config.get_config("ipv6", "pyrogram"),
            parse_mode=ParseMode.HTML,
            workers=config.get_config("workers", "pyrogram"),
            workdir="korone",
            sleep_threshold=180,
        )

        # Sudoers list
        self.sudoers = config.get_config("sudoers")

        # Bot startup time
        self.start_datetime = datetime.datetime.now().replace(tzinfo=datetime.UTC)

    async def start(self):
        await super().start()
        load_modules(self)

        if config.get_config("sentry_key"):
            log.info("[%s] Starting sentry.io integraion...", self.name)

            sentry_sdk.init(config.get_config("sentry_key"))

        # Save version info
        self.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])
        self.version = str((await shell_exec("git rev-parse --short HEAD"))[0])

        self.me = await self.get_me()
        log.info(
            "[%s] Running with Pyrogram v%s (Layer %s) started on @%s. Hi!",
            self.name,
            pyrogram.__version__,
            layer,
            self.me.username,
        )

        if config.get_config("backups_channel"):
            aiocron.crontab("0 * * * *", func=backup.save, args=(self,), start=True)
        else:
            log.info("[%s] Backups disabled.", self.name)

        try:
            if self.sudoers:
                for sudo in self.sudoers:
                    await self.send_message(
                        chat_id=sudo,
                        text=(
                            f"<b>Korone</b> <a href='https://github.com/AmanoTeam/PyKorone/commit/{self.version}'>"
                            f"{self.version}</a> (<code>{self.version_code}</code>) started! \n"
                            f"<b>Pyrogram</b> <code>v{pyrogram.__version__}</code> (Layer {layer})"
                        ),
                        disable_web_page_preview=True,
                    )
        except BadRequest:
            log.error(
                "[%s] Error while sending the startup message.",
                self.name,
                exc_info=True,
            )

    async def stop(self):
        await super().stop()
        log.warning("[%s] Stopped. Bye!", self.name)

    async def log(self, text: str, *args, **kwargs):
        await self.send_message(config.get_config("logs_channel"), text, *args, **kwargs)

    def is_sudo(self, user: User) -> bool:
        return user.id in self.sudoers
