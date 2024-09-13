# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import aiocron
import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import MessageIdInvalid, MessageNotModified
from hydrogram.raw.all import layer

from korone.config import ConfigManager
from korone.utils.backup import do_backup

from . import __version__
from .modules.core import load_all_modules
from .utils.caching import cache
from .utils.commands_list import set_ui_commands
from .utils.i18n import i18n
from .utils.logging import logger

if TYPE_CHECKING:
    from hydrogram.types import User


@dataclass(frozen=True, slots=True)
class AppParameters:
    api_id: str
    api_hash: str
    bot_token: str
    ipv6: bool = True
    name: str = "Korone"
    workers: int = 24


class Korone(Client):
    __slots__ = ("me", "parameters")

    def __init__(self, parameters: AppParameters):
        super().__init__(
            name=parameters.name,
            api_id=parameters.api_id,
            api_hash=parameters.api_hash,
            bot_token=parameters.bot_token,
            workers=parameters.workers,
            ipv6=parameters.ipv6,
            parse_mode=ParseMode.HTML,
            workdir=Path(__file__).parent.parent.as_posix(),
            sleep_threshold=180,
            max_concurrent_transmissions=2,
        )

        self.parameters = parameters
        self.me: User | None = None

    async def start(self) -> None:
        await super().start()

        await load_all_modules(self)
        await set_ui_commands(self, i18n)

        self.me = await self.get_me()

        await logger.ainfo(
            "Korone v%s running with Hydrogram v%s (Layer %s) started on @%s. Hi!",
            __version__,
            hydrogram.__version__,
            layer,
            self.me.username,
        )

        if backups_chat := ConfigManager.get("korone", "BACKUPS_CHAT"):
            aiocron.crontab("0 * * * *", do_backup, loop=self.loop, args=(self, backups_chat))

        if reboot_data := await cache.get("korone-reboot"):
            with suppress(MessageNotModified, MessageIdInvalid, KeyError):
                chat_id = reboot_data["chat_id"]
                message_id = reboot_data["message_id"]
                time_elapsed = round(time.time() - reboot_data["time"], 2)
                text = f"Rebooted in {time_elapsed} seconds."

                await self.edit_message_text(chat_id, message_id, text)

    async def stop(self) -> None:
        await super().stop()
        await logger.ainfo("Korone stopped.")
