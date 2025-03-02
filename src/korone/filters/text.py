# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import Message


class HasText(Filter):
    async def __call__(self, client: Client, update: Message) -> bool | None:
        return bool(update.text or update.caption)

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()  # type: ignore
