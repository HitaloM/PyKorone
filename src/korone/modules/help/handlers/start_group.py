from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.config import CONFIG
from korone.filters.chat_status import ChatTypeFilter
from korone.filters.cmd import CMDFilter
from korone.modules.help.callbacks import PMHelpStartUrlCallback
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.fsm.context import FSMContext


@flags.help(description=l_("Shows the start message"))
@flags.disableable(name="start")
class StartGroupHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("start"), ~ChatTypeFilter("private")

    async def handle(self) -> None:
        state: FSMContext = self.state

        await state.clear()

        buttons = InlineKeyboardBuilder()
        buttons.add(InlineKeyboardButton(text=f"ℹ️ {_('Help')}", url=PMHelpStartUrlCallback().pack()))
        buttons.add(InlineKeyboardButton(text=_("📢 Channel"), url=CONFIG.news_channel))

        text = _(
            "Hi, I'm Korone! An all-in-one bot. I can help you with lots of things. "
            "Just click on the buttons below to get started."
        )

        await self.event.reply(text, reply_markup=buttons.as_markup())
