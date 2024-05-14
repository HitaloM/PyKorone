# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import traceback

from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.types import Message
from meval import meval

from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.sudo.utils import build_text, generate_document
from korone.modules.utils.filters import Command, IsSudo
from korone.modules.utils.filters.command import CommandObject


class Evaluate(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["eval", "ev"]) & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        expression = command.args
        if not expression:
            await message.reply_text("No expression provided.")
            return

        try:
            output = await meval(expression, globals(), **locals())
        except Exception:
            traceback_string = traceback.format_exc()
            await message.reply_text(
                f"Exception while running the code:\n<pre>{traceback_string}</pre>"
            )
            return

        if not output:
            await message.reply_text("No output.")
            return

        if len(str(output)) > 4096:
            await generate_document(output, message)
            return

        await message.reply_text(build_text(str(output)), parse_mode=ParseMode.MARKDOWN)
