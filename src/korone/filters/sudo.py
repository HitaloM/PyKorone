# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.config import ConfigManager
from korone.utils.logging import logger


def load_sudoers() -> set[int]:
    sudoers = ConfigManager.get("korone", "SUDOERS")

    if not sudoers:
        msg = "The SUDOERS list was not loaded correctly. Please check your configuration file."
        logger.error(msg)
        raise ValueError(msg)

    if not isinstance(sudoers, list):
        msg = "The SUDOERS list must be a list. Please check your configuration file."
        logger.error(msg)
        raise TypeError(msg)

    if not all(isinstance(user_id, int) for user_id in sudoers):
        msg = "The SUDOERS list must contain only integers. Please check your configuration file."
        logger.error(msg)
        raise TypeError(msg)

    return set(sudoers)


SUDOERS = load_sudoers()


class IsSudo(Filter):
    __slots__ = ("client", "update")

    def __init__(self, client: Client, update: Message | CallbackQuery) -> None:
        self.client = client
        self.update = update

    async def __call__(self) -> bool:
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update

        user = update.from_user
        if user is None:
            await logger.awarning(
                "[Filters/Sudo] Update without originating user.", chat=message.chat.id
            )
            return False

        user_id = user.id
        chat_id = message.chat.id

        if user_id in SUDOERS:
            await logger.ainfo("[Filters/Sudo] Access granted.", user=user_id, chat=chat_id)
            return True

        await logger.awarning(
            "[Filters/Sudo] Unauthorized access attempt.", user=user_id, chat=chat_id
        )
        return False

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()
