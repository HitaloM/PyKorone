# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from abc import ABC, abstractmethod

from hydrogram import Client
from hydrogram.types import CallbackQuery


class CallbackQueryHandler(ABC):
    @abstractmethod
    async def handle(self, client: Client, callback: CallbackQuery) -> None: ...
