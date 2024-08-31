# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Regex
from korone.modules.regex.utils import SED_PATTERN, process_command
from korone.utils.i18n import gettext as _


@router.message(Regex(SED_PATTERN, friendly_name="sed"))
async def handle_sed(client: Client, message: Message) -> None:
    if not (match := re.match(SED_PATTERN, message.text)):
        return

    substitution_commands = match[0].split(";")
    original_text = message.reply_to_message.text if message.reply_to_message else ""
    modified_text = original_text

    for command in substitution_commands:
        command_data, error_message = process_command(command)
        if error_message:
            await message.reply(error_message)
            return

        if command_data is None:
            await message.reply(_("Invalid command data."))
            return

        from_pattern, to_pattern, flags, count = command_data

        try:
            modified_text = re.sub(
                from_pattern, to_pattern, modified_text, count=count, flags=flags
            )
        except re.error as e:
            await message.reply(_("Regex error: {e}").format(e=str(e)))
            return

    if not message.reply_to_message:
        await message.reply(_("No message to apply the substitution."))
        return

    if modified_text == original_text:
        await message.reply(_("Your regex didn't change anything from the original message."))
        return

    await client.send_message(
        message.chat.id, modified_text, reply_to_message_id=message.reply_to_message.id
    )
