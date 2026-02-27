from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ButtonStyle
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, Template, Url

from korone.config import CONFIG
from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.callbacks import PMHelpModules
from korone.modules.privacy import PrivacyMenuCallback
from korone.modules.utils_.callbacks import GoToStartCallback, LanguageButtonCallback
from korone.utils.handlers import KoroneMessageCallbackQueryHandler
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.fsm.context import FSMContext


@flags.help(exclude=True)
class StartPMHandler(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(cls, CommandStart(), PrivateChatFilter())
        router.callback_query.register(cls, PrivateChatFilter(), GoToStartCallback.filter())

    async def handle(self) -> None:
        state: FSMContext = self.state

        await state.clear()

        i18n = get_i18n()
        current_locale_flag = i18n.current_locale_display.split(" ", 1)[0]

        builder = InlineKeyboardBuilder()
        builder.button(text=_("🕵️‍♂️ Privacy"), callback_data=PrivacyMenuCallback(back_to_start=True))
        builder.button(text=f"{current_locale_flag} {_('Language')}", callback_data=LanguageButtonCallback())
        builder.button(text=_("ℹ️ Help"), style=ButtonStyle.PRIMARY, callback_data=PMHelpModules(back_to_start=True))
        builder.adjust(2, 1)
        buttons = builder.as_markup()

        text = Doc(
            _(
                "Hi, I'm Korone, your all-in-one assistant. "
                "Use the buttons below to open help, privacy, and language settings."
            ),
            Template(
                _("Join my {channel} for update announcements and feature news."),
                channel=Url(_("news channel"), CONFIG.news_channel),
            ),
        )

        await self.answer(str(text), reply_markup=buttons)
