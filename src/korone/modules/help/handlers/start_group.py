from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import CommandStart
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.config import CONFIG
from korone.filters.chat_status import GroupChatFilter
from korone.modules.help.callbacks import HELP_START_PAYLOAD
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.fsm.context import FSMContext


@flags.help(description=l_("Show the start message."))
@flags.disableable(name="start")
class StartGroupHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CommandStart(), GroupChatFilter()

    async def handle(self) -> None:
        state: FSMContext = self.state

        await state.clear()
        help_url = await create_start_link(self.bot, HELP_START_PAYLOAD)

        buttons = InlineKeyboardBuilder()
        buttons.button(text=f"ℹ️ {_('Help')}", url=help_url)
        buttons.button(text=_("📢 Channel"), url=CONFIG.news_channel)
        buttons.adjust(2)

        text = _(
            "Hi, I'm Korone, your all-in-one bot for this chat. Use the buttons below to open help and follow updates."
        )

        await self.event.reply(text, reply_markup=buttons.as_markup())
