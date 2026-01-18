from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.help.callbacks import PMHelpStartUrlCallback
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.disableable(name="help")
@flags.help(description=l_("Shows the help message"))
class HelpGroupHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("help"), ~ChatTypeFilter("private")

    async def handle(self) -> Any:
        text = _("The help information available in the private messages with Sophie")

        buttons = InlineKeyboardBuilder()
        buttons.add(InlineKeyboardButton(text=f"ℹ️ {_('Help')}", url=PMHelpStartUrlCallback().pack()))

        await self.event.reply(str(text), reply_markup=buttons.as_markup())
