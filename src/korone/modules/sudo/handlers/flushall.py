# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time

from hydrogram import Client
from hydrogram.types import Message

from korone import cache
from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.utils.filters import Command, IsSudo


class PurgeCache(MessageHandler):
    @staticmethod
    @router.message(Command("flushall", disableable=False) & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        start_time = time.time()
        start = await message.reply_text("Flushing cache...")
        await cache.clear()
        await start.edit_text(f"Cache flushed in {time.time() - start_time:.2f} seconds.")
