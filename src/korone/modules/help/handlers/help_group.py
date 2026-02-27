from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.filters.chat_status import GroupChatFilter
from korone.modules.help.callbacks import HELP_START_PAYLOAD
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.disableable(name="help")
@flags.help(description=l_("Open help in private chat."))
class HelpGroupHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return Command("help"), GroupChatFilter()

    async def handle(self) -> None:
        text = _("Detailed help is available in private chat with Korone.")
        help_url = await create_start_link(self.bot, HELP_START_PAYLOAD)

        buttons = InlineKeyboardBuilder()
        buttons.button(text=f"ℹ️ {_('Help')}", url=help_url)

        await self.event.reply(str(text), reply_markup=buttons.as_markup())
