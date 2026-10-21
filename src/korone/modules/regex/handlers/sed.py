import re
from typing import TYPE_CHECKING

from aiogram import flags

from korone.modules.regex.utils import SED_PATTERN, SedPatternFilter, process_command
from korone.modules.utils_.reply_or_edit import reply_message
from korone.ui import template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(
    description=l_("Apply a sed-style regex substitution to a replied message."),
    cmds=("s/old/new/flags",),
    raw_cmds=True,
)
@flags.disableable(name="sed")
class SedHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (SedPatternFilter(SED_PATTERN),)

    async def handle(self) -> None:
        text = self.event.text
        if not text:
            return

        replied_message = self.event.reply_to_message
        if not replied_message:
            await self.answer(_("No message to apply the substitution."))
            return

        original_text = replied_message.text or replied_message.caption or ""
        if not original_text:
            await self.answer(_("No text to apply the substitution."))
            return

        match = re.match(SED_PATTERN, text)
        if not match:
            return

        substitution_commands = match[0].split(";")
        modified_text = original_text

        for command in substitution_commands:
            command_data, error_message = process_command(command)
            if error_message:
                await self.answer(error_message)
                return

            if command_data is None:
                await self.answer(_("Invalid command data."))
                return

            from_pattern, to_pattern, flags, count = command_data

            try:
                modified_text = re.sub(from_pattern, to_pattern, modified_text, count=count, flags=flags)
            except re.error as e:
                await self.answer(template(_("Regex error: {e}"), e=str(e)))
                return

        if modified_text == original_text:
            await self.answer(_("Your regex didn't change anything from the original message."))
            return

        if not modified_text.strip():
            await self.answer(_("The substitution produced an empty message."))
            return

        await reply_message(replied_message, modified_text)
