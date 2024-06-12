# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import traceback

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.types import Message
from meval import meval

from korone.decorators import router
from korone.filters import Command, CommandObject, IsSudo
from korone.handlers.abstract import MessageHandler
from korone.modules.sudo.utils import build_text, generate_document


class Evaluate(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["eval", "ev"], disableable=False) & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        expression = command.args
        if not expression:
            await message.reply("No expression provided.")
            return

        async with ChatActionSender(client=client, chat_id=message.chat.id, initial_sleep=3.0):
            try:
                output = await meval(expression, globals(), **locals())
            except Exception:
                traceback_string = traceback.format_exc()
                await message.reply(
                    f"Exception while running the code:\n<pre>{traceback_string}</pre>"
                )
                return

            if not output:
                await message.reply("No output.")
                return

            if len(str(output)) > 4096:
                await generate_document(output, message)
                return

            await message.reply(build_text(str(output)), parse_mode=ParseMode.MARKDOWN)
