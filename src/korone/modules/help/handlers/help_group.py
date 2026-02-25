from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.filters.chat_status import GroupChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.help.callbacks import PMHelpStartUrlCallback
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.disableable(name="help")
@flags.help(description=l_("Shows the help message"))
class HelpGroupHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("help"), GroupChatFilter()

    async def handle(self) -> None:
        text = _("The help information available in the private messages with Korone")

        buttons = InlineKeyboardBuilder()
        buttons.button(text=f"ℹ️ {_('Help')}", url=PMHelpStartUrlCallback().pack())

        await self.event.reply(str(text), reply_markup=buttons.as_markup())
