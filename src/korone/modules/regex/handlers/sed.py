# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import regex as re
from hydrogram import Client, filters
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.modules.regex.utils import (
    MAX_PATTERN_LENGTH,
    SED_PATTERN,
    build_flags_and_count,
    cleanup_pattern,
)
from korone.utils.i18n import gettext as _


class SedHandler(MessageHandler):
    @staticmethod
    def substitute(text: str, from_pattern: str, to_pattern: str, flags: int, count: int) -> str:
        return re.sub(from_pattern, to_pattern, text, count=count, flags=flags)

    async def process_message(self, client: Client, message: Message, match: re.Match) -> None:
        from_pattern, to_pattern = cleanup_pattern(match)
        flags_str = (match.group(3) or "")[1:]
        try:
            flags, count = build_flags_and_count(flags_str)
        except ValueError as e:
            await message.reply(_("Unknown flag: {flag}").format(flag=e.args[1]))
            return

        if len(from_pattern) > MAX_PATTERN_LENGTH or len(to_pattern) > MAX_PATTERN_LENGTH:
            await message.reply(_("Pattern is too long. Please use shorter patterns."))
            return

        try:
            if message.reply_to_message:
                original_msg = message.reply_to_message
                substitution = self.substitute(
                    original_msg.text, from_pattern, to_pattern, flags, count
                )
                if substitution:
                    await client.send_message(
                        message.chat.id, substitution, reply_to_message_id=original_msg.id
                    )
                    return
            await message.reply(_("No message to apply the substitution."))
        except re.error as e:
            await message.reply(_("Regex error: {e}").format(e=str(e)))
        except Exception as e:
            await message.reply(_("Unexpected error: {e}").format(e=str(e)))

    @router.message(filters.regex(SED_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        match = re.match(SED_PATTERN, message.text)
        if match:
            await self.process_message(client, message, match)
