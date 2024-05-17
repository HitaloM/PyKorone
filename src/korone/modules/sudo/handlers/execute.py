# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
import traceback
from contextlib import redirect_stdout

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.sudo.utils import build_text, generate_document
from korone.modules.utils.filters import Command, CommandObject, IsSudo


class Execute(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["exec", "ex"], disableable=False) & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        code = command.args
        if not code:
            await message.reply_text("No expression provided.")
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
                    await message.reply_text(
                        build_text(traceback.format_exc()), parse_mode=ParseMode.MARKDOWN
                    )
                    return

            output = strio.getvalue()
            if not output:
                await message.reply_text("No output.")
                return

            if len(output) > 4096:
                await generate_document(output, message)
                return

            await message.reply_text(build_text(str(output)), parse_mode=ParseMode.MARKDOWN)
