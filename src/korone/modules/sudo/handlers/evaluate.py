# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
import traceback
from typing import Any

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.types import Message
from meval import meval

from korone.constants import MESSAGE_LENGTH_LIMIT
from korone.decorators import router
from korone.filters import Command, CommandObject, IsSudo
from korone.modules.sudo.utils import generate_document


@router.message(Command(commands=["eval", "ev"], disableable=False) & IsSudo)
async def eval_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    expression = command.args
    if not expression:
        await message.reply("No expression provided.")
        return

    async with ChatActionSender(client=client, chat_id=message.chat.id, initial_sleep=3.0):
        try:
            output: Any = await meval(expression, globals(), **locals())
        except Exception:
            traceback_string = traceback.format_exc()
            await message.reply(
                "Exception while running the code:\n"
                f"<pre language='bash'>{html.escape(traceback_string)}</pre>"
            )
            return

        match output:
            case None:
                await message.reply("No output.")
            case output if len(str(output)) > MESSAGE_LENGTH_LIMIT:
                await generate_document(output, message)
            case _:
                await message.reply(f"<pre language='bash'>{html.escape(str(output))}</pre>")
