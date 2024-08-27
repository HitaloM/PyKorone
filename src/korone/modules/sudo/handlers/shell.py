# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import html

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsSudo
from korone.modules.sudo.utils import generate_document, run_command


@router.message(Command(commands=["shell", "sh"], disableable=False) & IsSudo)
async def shell_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse().args
    if not command:
        await message.reply("No command provided.")
        return

    async with ChatActionSender(client=client, chat_id=message.chat.id, initial_sleep=3.0):
        output = await run_command(command)

    if not output:
        await message.reply("No output.")
        return

    if len(output) > 4096:
        await generate_document(output, message)
        return

    await message.reply(f"<pre language='bash'>{html.escape(str(output))}</pre>")
