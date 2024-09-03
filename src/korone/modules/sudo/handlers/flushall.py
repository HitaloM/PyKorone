# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.utils.caching import cache


@router.message(Command("flushall", disableable=False) & IsSudo)
async def flushall_command(client: Client, message: Message) -> None:
    start_time = time.time()
    start = await message.reply("Flushing cache...")
    await cache.clear()
    await start.edit(f"Cache flushed in {time.time() - start_time:.2f} seconds.")
