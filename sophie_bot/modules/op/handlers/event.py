from __future__ import annotations

import ujson
from aiogram import flags
from stfu_tg import Code

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Prints the message event as JSON."))
class EventHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter(("event",)), IsOP(True))

    async def handle(self):
        event_data = self.event.model_dump(mode="json")
        text = ujson.dumps(event_data, indent=2)

        await self.event.reply(str(Code(text)))
