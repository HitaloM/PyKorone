from __future__ import annotations

import orjson
from aiogram import flags
from stfu_tg import Code

from korone.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Prints the message event as JSON."))
class EventHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple:
        return (CMDFilter(("event",)), IsOP(is_op=True))

    async def handle(self) -> None:
        event_data = self.event.model_dump(mode="json")
        text = orjson.dumps(event_data, option=orjson.OPT_INDENT_2).decode()

        # Split message if it exceeds Telegram's limit
        if len(text) <= TELEGRAM_MESSAGE_LENGTH_LIMIT:
            await self.event.reply(str(Code(text)))
        else:
            # Split into chunks that fit within the limit accounting for Code formatting
            # Code adds some overhead, so we use a slightly smaller chunk size
            max_chunk_size = TELEGRAM_MESSAGE_LENGTH_LIMIT - 20  # Account for formatting
            chunks = [text[i : i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]

            for chunk in chunks:
                await self.event.reply(str(Code(chunk)))
