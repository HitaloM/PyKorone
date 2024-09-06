# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.config import ConfigManager
from korone.utils.logging import logger

SUDOERS = ConfigManager.get("korone", "SUDOERS")

if not SUDOERS:
    msg = "The SUDOERS list has not been loaded correctly. Check your configuration file."
    logger.error(msg)
    raise ValueError(msg)

if not isinstance(SUDOERS, list) or not all(isinstance(i, int) for i in SUDOERS):
    msg = "The SUDOERS list must be a list of integers. Check your configuration file."
    logger.error(msg)
    raise TypeError(msg)


class IsSudo(Filter):
    __slots__ = ("client", "update")

    def __init__(self, client: Client, update: Message | CallbackQuery) -> None:
        self.client = client
        self.update = update

    async def __call__(self) -> bool:
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update

        if message.from_user is None:
            return False

        user_id = message.from_user.id
        chat_id = message.chat.id
        if user_id in SUDOERS:
            await logger.ainfo(
                "[Filters/Sudo] Access allowed for user %s in %s.", user_id, chat_id
            )
            return True
        await logger.awarning(
            "[Filters/Sudo] Unauthorized access attempt by user %s in %s.", user_id, chat_id
        )
        return False

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()
