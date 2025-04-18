# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import Message


class HasText(Filter):
    """Filter messages that contain either text or caption.

    This filter checks if a message object has either a text or caption field with content.
    Useful for filters that need to process text regardless of where it appears in a message.
    """

    async def __call__(self, client: Client, update: Message) -> bool:
        """Check if the message has text or caption.

        Args:
            client: The client instance
            update: The message to check

        Returns:
            bool: True if the message contains text or caption, False otherwise
        """
        return bool(update.text or update.caption)

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()  # type: ignore
