# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import regex as re
from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Regex
from korone.handlers.abstract import MessageHandler
from korone.modules.regex.utils import SED_PATTERN, process_command
from korone.utils.i18n import gettext as _


class SedHandler(MessageHandler):
    @router.message(Regex(SED_PATTERN, friendly_name="sed"))
    async def handle(self, client: Client, message: Message) -> None:
        match = re.match(SED_PATTERN, message.text)
        if match:
            await self.process_message(client, message, match)

    @staticmethod
    async def process_message(client: Client, message: Message, match: re.Match) -> None:
        substitution_commands = match.group(0).split(";")
        original_text = message.reply_to_message.text if message.reply_to_message else ""
        modified_text = original_text

        for command in substitution_commands:
            command_data, error_message = process_command(command)
            if error_message:
                await message.reply(error_message)
                return

            from_pattern, to_pattern, flags, count = command_data

            try:
                modified_text = re.sub(
                    from_pattern, to_pattern, modified_text, count=count, flags=flags
                )
            except re.error as e:
                await message.reply(_("Regex error: {e}").format(e=str(e)))
                return

        if modified_text != original_text and message.reply_to_message:
            await client.send_message(
                message.chat.id, modified_text, reply_to_message_id=message.reply_to_message.id
            )
        elif modified_text == original_text:
            await message.reply(_("Your regex didn't change anything from the original message."))
        else:
            await message.reply(_("No message to apply the substitution."))
