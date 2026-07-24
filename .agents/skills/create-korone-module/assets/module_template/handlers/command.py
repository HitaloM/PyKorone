from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Run the example command."))
class ExampleHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("example"),)

    async def handle(self) -> None:
        await self.event.reply(_("Example response"))
