from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ButtonStyle
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.config import CONFIG
from korone.filters.chat_status import PrivateChatFilter
from korone.modules.privacy.callbacks import PrivacyMenuCallback
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.utils.handlers import KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router


@flags.help(description=l_("Shows the privacy policy of the bot"))
class PrivacyMenu(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(cls, Command("privacy"), PrivateChatFilter())
        router.callback_query.register(cls, PrivacyMenuCallback.filter())

    async def handle(self) -> None:
        callback_data: PrivacyMenuCallback | None = self.data.get("callback_data", None)

        text = _("The privacy policy of the bot is available on our wiki page.")
        buttons = InlineKeyboardBuilder()
        buttons.button(text=_("Privacy Policy"), url=CONFIG.privacy_link)

        if callback_data and callback_data.back_to_start:
            buttons.button(text=_("⬅️ Back"), style=ButtonStyle.PRIMARY, callback_data=GoToStartCallback())

        buttons.adjust(1)

        await self.answer(text, reply_markup=buttons.as_markup())
