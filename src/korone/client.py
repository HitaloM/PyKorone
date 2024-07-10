# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import MessageIdInvalid, MessageNotModified
from hydrogram.raw.all import layer

from korone import __version__, cache, constants
from korone.database.sqlite import SQLite3Connection
from korone.modules import load_all_modules
from korone.utils.logging import log

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
        self.parameters = parameters
        self.me: User

        super().__init__(
            name=self.parameters.name,
            api_id=self.parameters.api_id,
            api_hash=self.parameters.api_hash,
            bot_token=self.parameters.bot_token,
            workers=self.parameters.workers,
            ipv6=self.parameters.ipv6,
            parse_mode=ParseMode.HTML,
            workdir=Path(__file__).parent.parent.as_posix(),
            sleep_threshold=180,
            max_concurrent_transmissions=2,
        )

    async def start(self) -> None:
        await super().start()

        self.me = await self.get_me()

        async with SQLite3Connection() as conn:
            await conn.execute(constants.SQLITE3_TABLES, script=True)
            await conn.vacuum()

        await load_all_modules(self)

        log.info(
            "Korone %s running with Hydrogram v%s (Layer %s) started on @%s. Hi!",
            __version__,
            hydrogram.__version__,
            layer,
            self.me.username,
        )

        cache_key = "korone-reboot"
        if reboot_data := await cache.get(cache_key):
            with suppress(MessageNotModified, MessageIdInvalid, KeyError):
                chat_id = reboot_data["chat_id"]
                message_id = reboot_data["message_id"]
                time_elapsed = round(time.time() - reboot_data["time"], 2)
                text = f"Rebooted in {time_elapsed} seconds."

                await self.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)

            await cache.delete(cache_key)

    async def stop(self) -> None:
        await super().stop()
        log.info("Korone stopped.")
