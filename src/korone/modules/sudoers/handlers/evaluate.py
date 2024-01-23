# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import traceback

from hydrogram import Client, filters
from hydrogram.enums import ParseMode
from hydrogram.types import Message
from meval import meval

from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.sudoers.utils import build_text, generate_document
from korone.modules.utils.commands import get_command_arg
from korone.modules.utils.filters import is_sudo


class Evaluate(MessageHandler):
    @router.message(filters.command(["eval", "ev"]) & is_sudo)
    async def handle(self, client: Client, message: Message) -> None:
        expression = get_command_arg(message)
        if not expression:
            await message.reply_text("No expression provided.")
            return

        try:
            output = await meval(expression, globals(), **locals())
        except BaseException:
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
