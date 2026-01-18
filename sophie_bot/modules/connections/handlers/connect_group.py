from __future__ import annotations

from aiogram import flags
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from sophie_bot.config import CONFIG
from sophie_bot.modules.connections.utils.connection import (
    check_connection_permissions,
    get_connection_text,
    get_disconnect_markup,
    set_connected_chat,
)
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter


@flags.help(description=l_("Connects to the current chat."))
class ConnectGroupCmd(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("connect"), ChatTypeFilter("group", "supergroup"))

    async def handle(self):
        if not self.event.from_user:
            return
        user_id = self.event.from_user.id
        chat_id = self.event.chat.id

        # Check permissions
        if not await check_connection_permissions(chat_id, user_id):
            await self.event.reply(_("You are not allowed to connect to this chat."))
            return

        await set_connected_chat(user_id, chat_id)
        text = await get_connection_text(chat_id)
        markup = get_disconnect_markup()

        try:
            await self.bot.send_message(user_id, str(text), reply_markup=markup)
            await self.event.reply(
                _("You are connected! Check your DM with Sophie."),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text=_("Open DM"), url=f"https://t.me/{CONFIG.username}")]]
                ),
            )
        except TelegramForbiddenError:
            await self.event.reply(
                _(
                    "You must start the bot in DM first to connect. Once you initialize connection with Sophie, you'll be connected."
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=_("Start Sophie"), url=f"https://t.me/{CONFIG.username}?start=connect_{chat_id}"
                            )
                        ]
                    ]
                ),
            )
