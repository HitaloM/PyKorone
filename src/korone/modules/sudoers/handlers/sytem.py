# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import asyncio
import os
import sys
import time
from signal import SIGINT

from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.types import Message

from korone import redis
from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.sudoers.utils import build_text, generate_document
from korone.modules.utils.filters import Command, IsSudo
from korone.modules.utils.filters.command import CommandObject


class Reboot(MessageHandler):
    @staticmethod
    @router.message(Command("reboot") & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        await message.reply_text("Rebooting...")
        os.execv(sys.executable, [sys.executable, "-m", "korone"])


class Shutdown(MessageHandler):
    @staticmethod
    @router.message(Command("shutdown") & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        await message.reply_text("Shutting down...")
        os.kill(os.getpid(), SIGINT)


class Shell(MessageHandler):
    @staticmethod
    async def run_command(command: str) -> str:
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return (stdout + stderr).decode()

    @router.message(Command(commands=["shell", "sh"]) & IsSudo)
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse().args
        if not command:
            await message.reply_text("No command provided.")
            return

        output = await self.run_command(command)

        if not output:
            await message.reply_text("No output.")
            return

        if len(output) > 4096:
            await generate_document(output, message)
            return

        await message.reply_text(build_text(output), parse_mode=ParseMode.MARKDOWN)


class PurgeCache(MessageHandler):
    @staticmethod
    @router.message(Command("flushall") & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        start_time = time.time()
        start = await message.reply_text("Flushing cache...")
        await redis.flushall()
        await start.edit_text(f"Cache flushed in {time.time() - start_time:.2f} seconds.")
