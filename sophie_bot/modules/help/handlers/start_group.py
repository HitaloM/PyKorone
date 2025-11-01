from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, Template, Url

from sophie_bot.config import CONFIG
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.message_status import NoArgs
from sophie_bot.modules.help.callbacks import PMHelpStartUrlCallback
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows the start message"))
@flags.disableable(name="start")
class StartGroupHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("start"), ~ChatTypeFilter("private"), NoArgs(True)

    async def handle(self) -> Any:
        state: FSMContext = self.state

        # Reset current state
        await state.clear()

        buttons = InlineKeyboardBuilder()
        buttons.add(InlineKeyboardButton(text=f"ℹ️ {_('Help')}", url=PMHelpStartUrlCallback().pack()))

        text = Doc(
            _("My name is Sophie, I help manage this group in an efficient way!"),
            Template(
                _("Join the {chat} and {channel}."),
                chat=Url(_("💬 Support Chat"), CONFIG.support_link),
                channel=Url(_("📢 NEWS Channel"), CONFIG.news_channel),
            ),
        )

        await self.event.reply(
            str(text), reply_markup=buttons.as_markup(), link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
