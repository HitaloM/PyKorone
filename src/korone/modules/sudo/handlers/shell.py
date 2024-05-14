# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio

from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.sudo.utils import build_text, generate_document
from korone.modules.utils.filters import Command, IsSudo
from korone.modules.utils.filters.command import CommandObject


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
