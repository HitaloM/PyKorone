from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Causes the bot to crash (for testing purposes)."))
class CrashHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("op_crash"), IsOP(is_op=True))

    async def handle(self) -> None:
        await self.event.reply("Crashing...")

        _ = 1 / 0
