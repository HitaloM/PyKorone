# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import os
import sys
import time

from hydrogram import Client
from hydrogram.types import Message

from korone import cache
from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.utils.filters import Command, IsSudo


class Reboot(MessageHandler):
    @staticmethod
    @router.message(Command("reboot") & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        cache_key = "korone-reboot"
        if await cache.get(cache_key):
            await cache.delete(cache_key)

        sent = await message.reply_text("Rebooting...")

        value = {"chat_id": message.chat.id, "message_id": sent.id, "time": time.time()}
        await cache.set(cache_key, value=value, expire=300)

        os.execv(sys.executable, [sys.executable, "-m", "korone"])
