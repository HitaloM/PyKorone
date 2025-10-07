# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiocron
import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import MessageIdInvalid, MessageNotModified
from hydrogram.raw.all import layer

from korone import constants
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
    """Parameters required for initializing the bot client.

    This dataclass holds all configuration parameters needed for the Hydrogram client.
    """

    api_id: str
    api_hash: str
    bot_token: str
    ipv6: bool = True
    name: str = "Korone"
    workers: int = 24


class Korone(Client):
    """The main bot client class extending Hydrogram Client.

    Handles client initialization, starting and stopping processes.
    """

    __slots__ = ("me", "parameters")

    def __init__(self, parameters: AppParameters) -> None:
        """Initialize the bot client.

        Args:
            parameters: Configuration parameters for the client
        """
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
        """Start the bot client and initialize all required components."""
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

        backups_chat = ConfigManager.get("korone", "BACKUPS_CHAT")
        if backups_chat:
            aiocron.crontab("0 * * * *", do_backup, loop=self.loop, args=(self, backups_chat))

        reboot_data: dict[str, Any] | None = await cache.get(constants.REBOOT_CACHE_KEY)
        if reboot_data:
            with suppress(MessageNotModified, MessageIdInvalid, KeyError):
                chat_id = reboot_data["chat_id"]
                message_id = reboot_data["message_id"]
                time_elapsed = round(time.time() - reboot_data["time"], 2)
                text = f"Rebooted in {time_elapsed} seconds."

                await self.edit_message_text(chat_id, message_id, text)

    async def stop(self) -> None:
        """Stop the bot client and perform cleanup."""
        await super().stop()
        await logger.ainfo("Korone stopped.")
