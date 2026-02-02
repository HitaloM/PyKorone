from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aiogram import flags

from korone.modules.regex.utils import SED_PATTERN, SedPatternFilter, process_command
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(
    description=l_("Apply a regex substitution to a replied message."), cmds=("s/old/new/flags",), raw_cmds=True
)
@flags.disableable(name="sed")
class SedHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (SedPatternFilter(SED_PATTERN),)

    async def handle(self) -> None:
        message = self.event
        text = message.text
        if not text:
            return

        reply_message = message.reply_to_message
        if not reply_message:
            await message.reply(_("No message to apply the substitution."))
            return

        original_text = reply_message.text or reply_message.caption or ""
        if not original_text:
            await message.reply(_("No text to apply the substitution."))
            return

        match = re.match(SED_PATTERN, text)
        if not match:
            return

        substitution_commands = match[0].split(";")
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
                modified_text = re.sub(from_pattern, to_pattern, modified_text, count=count, flags=flags)
            except re.error as e:
                await message.reply(_("Regex error: {e}").format(e=str(e)))
                return

        if modified_text == original_text:
            await message.reply(_("Your regex didn't change anything from the original message."))
            return

        bot = message.bot
        if not bot:
            return

        await bot.send_message(message.chat.id, modified_text, reply_to_message_id=reply_message.message_id)
