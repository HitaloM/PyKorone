from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.types import Message
from magic_filter import F

from korone.modules.language.callbacks import LangMenu, LangMenuCallback
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(exclude=True)
class LanguageCancelHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (LangMenuCallback.filter(F.menu == LangMenu.Cancel),)

    async def handle(self) -> None:
        message = self.event.message

        if isinstance(message, Message):
            await message.edit_text(
                _("Changing language was canceled. You can change language again by using /language command.")
            )
