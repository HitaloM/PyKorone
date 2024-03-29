# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import io
import traceback
from contextlib import redirect_stdout

from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.sudoers.utils import build_text, generate_document
from korone.modules.utils.filters import Command, IsSudo
from korone.modules.utils.filters.command import CommandObject


class Execute(MessageHandler):
    @router.message(Command(commands=["exec", "ex"]) & IsSudo)
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        code = command.args
        if not code:
            await message.reply_text("No expression provided.")
            return

        reply = message.reply_to_message
        user = (reply or message).from_user
        chat = message.chat

        code_function = "\n".join(
            ["async def __ex(client, message, reply, user, chat):"]
            + [f"    {line}" for line in code.split("\n")]
        )
        exec(code_function)

        strio = io.StringIO()
        with redirect_stdout(strio):
            try:
                await locals()["__ex"](client, message, reply, user, chat)
            except BaseException:
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
