from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, Template, Url

from korone.config import CONFIG
from korone.filters.chat_status import ChatTypeFilter
from korone.filters.cmd import CMDFilter
from korone.modules.help.callbacks import PMHelpModules
from korone.modules.privacy import PrivacyMenuCallback
from korone.modules.utils_.callbacks import GoToStartCallback, LanguageButtonCallback
from korone.utils.handlers import KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.fsm.context import FSMContext


@flags.help(exclude=True)
class StartPMHandler(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(cls, CMDFilter("start"), ChatTypeFilter("private"))
        router.callback_query.register(cls, ChatTypeFilter("private"), GoToStartCallback.filter())

    async def handle(self) -> None:
        state: FSMContext = self.state

        await state.clear()

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=_("🕵️‍♂️ Privacy"), callback_data=PrivacyMenuCallback(back_to_start=True).pack()),
            InlineKeyboardButton(text=_("🌍 Language"), callback_data=LanguageButtonCallback().pack()),
        )
        builder.row(InlineKeyboardButton(text=_("ℹ️ Help"), callback_data=PMHelpModules(back_to_start=True).pack()))
        buttons = builder.as_markup()

        text = Doc(
            _(
                "Hi, I'm Korone! An all-in-one bot. I can help you with lots of things. "
                "Just click on the buttons below to get started."
            ),
            Template(
                _("Join my {channel} to get information on all the latest updates."),
                channel=Url(_("news channel"), CONFIG.news_channel),
            ),
        )

        await self.answer(str(text), reply_markup=buttons)
