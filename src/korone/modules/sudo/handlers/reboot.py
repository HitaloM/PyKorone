# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import os
import sys

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.utils.filters import Command, IsSudo


class Reboot(MessageHandler):
    @staticmethod
    @router.message(Command("reboot") & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        await message.reply_text("Rebooting...")
        os.execv(sys.executable, [sys.executable, "-m", "korone"])
