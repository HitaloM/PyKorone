# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import os
from signal import SIGINT

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo


@router.message(Command("shutdown", disableable=False) & IsSudo)
async def shutdown_command(client: Client, message: Message) -> None:
    await message.reply("Shutting down...")
    os.kill(os.getpid(), SIGINT)
