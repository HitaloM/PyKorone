from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from magic_filter import F

from korone.modules.language.callbacks import LangMenu, LangMenuCallback
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _


@flags.help(exclude=True)
class LanguageCancelHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (LangMenuCallback.filter(F.menu == LangMenu.Cancel),)

    async def handle(self) -> Any:
        message = self.event.message

        if isinstance(message, Message):
            await message.edit_text(
                _("Changing language was canceled. You can change language again by using /language command.")
            )
