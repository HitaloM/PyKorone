from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows all lockable entities"))
@flags.disableable(name="lockable")
class ListLockableHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lockable"),)

    async def handle(self) -> Any:
        pass
