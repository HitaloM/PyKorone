# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.piston.utils.api import create_request, get_languages, run_code
from korone.utils.i18n import gettext as _


@router.message(Command("piston"))
async def piston_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args:
        await message.reply(
            _(
                "You need to provide a command to run. "
                "Example: <code>/piston python print('Hello, World!')</code>"
            )
        )
        return

    languages = await get_languages()
    if not languages:
        await message.reply(_("Failed to fetch the available languages."))
        return

    if command.args.split()[0] not in languages:
        await message.reply(
            _("Invalid language. Use <code>/pistonlangs</code> to see the available languages.")
        )
        return

    async with ChatActionSender(client=client, chat_id=message.chat.id, action=ChatAction.TYPING):
        request = create_request(command.args)
        response = await run_code(request)

        if response.result == "error":
            await message.reply(_("An error occurred while running the code."))
            return

        text = _("<b>Code</b>:\n<pre language='{lang}'>{code}</pre>\n\n").format(
            lang=command.args.split()[0], code=request.code
        )

        if response.output:
            text += _("<b>Output</b>:\n<pre language='bash'>{output}</pre>\n").format(
                output=response.output
            )

        if response.compiler_output:
            text += _("<b>Compiler Output</b>:\n<pre language='bash'>{output}</pre>").format(
                output=response.compiler_output
            )

        await message.reply(text, disable_web_page_preview=True)