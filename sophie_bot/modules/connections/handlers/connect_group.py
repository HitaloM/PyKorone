from __future__ import annotations

from aiogram import flags
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from stfu_tg import Doc, Title, Template

from sophie_bot.config import CONFIG
from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.modules.connections.utils.constants import CONNECTION_DISCONNECT_TEXT
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_connection_settings import ChatConnectionSettingsModel
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.modules.utils_.admin import is_user_admin
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
        if not await self.check_permissions(chat_id, user_id):
            await self.event.reply(_("You are not allowed to connect to this chat."))
            return

        await set_connected_chat(user_id, chat_id)
        chat = await ChatModel.get_by_tid(chat_id)

        text = Doc(
            Title(_("Connected!")),
            Template(_("Connected to {chat_name}."), chat_name=chat.first_name_or_title if chat else str(chat_id)),
            _("⚠️ The connection feature is obsolete in favor of the web app."),
            _("⏳ This connection will last for 48 hours."),
        )

        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(CONNECTION_DISCONNECT_TEXT))]], resize_keyboard=True
        )

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

    async def check_permissions(self, chat_id, user_id):
        # Admins always allowed
        if await is_user_admin(chat_id, user_id):
            return True

        # Check settings
        settings = await ChatConnectionSettingsModel.get_by_chat_id(chat_id)
        if settings and not settings.allow_users_connect:
            return False

        return True
