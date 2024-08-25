# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import os
import sys
import time

from hydrogram import Client
from hydrogram.types import Message

from korone import cache
from korone.decorators import router
from korone.filters import Command, IsSudo


@router.message(Command("reboot", disableable=False) & IsSudo)
async def reboot_command(client: Client, message: Message) -> None:
    cache_key = "korone-reboot"
    if await cache.get(cache_key):
        await cache.delete(cache_key)

    sent = await message.reply("Rebooting...")

    value = {"chat_id": message.chat.id, "message_id": sent.id, "time": time.time()}
    await cache.set(cache_key, value=value, expire=300)

    os.execv(sys.executable, [sys.executable, "-m", "korone"])
