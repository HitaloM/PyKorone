# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import html
import io
import traceback
from contextlib import redirect_stdout

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsSudo
from korone.modules.sudo.utils import generate_document


@router.message(Command(commands=["exec", "ex"], disableable=False) & IsSudo)
async def exec_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    code = command.args
    if not code:
        await message.reply("No expression provided.")
        return

    reply = message.reply_to_message
    user = (reply or message).from_user
    chat = message.chat

    async with ChatActionSender(client=client, chat_id=message.chat.id, initial_sleep=3.0):
        code_function = "\n".join(
            ["async def __ex(client, message, reply, user, chat):"]
            + [f"    {line}" for line in code.split("\n")]
        )
        exec(code_function)

        strio = io.StringIO()
        with redirect_stdout(strio):
            try:
                await locals()["__ex"](client, message, reply, user, chat)
            except Exception:
                traceback_string = traceback.format_exc()
                await message.reply(f"<pre language='bash'>{html.escape(traceback_string)}</pre>")
                return

        output = strio.getvalue()
        if not output:
            await message.reply("No output.")
            return

        if len(output) > 4096:
            await generate_document(output, message)
            return

        await message.reply(f"<pre language='bash'>{html.escape(str(output))}</pre>")
