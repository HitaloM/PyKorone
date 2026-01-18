from __future__ import annotations

from re import search
from typing import Any

from aiogram import F, flags
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from stfu_tg import Doc, Title, Template, Section

from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.modules.connections.utils.constants import CONNECTION_DISCONNECT_TEXT
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_connection_settings import ChatConnectionSettingsModel
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.utils.i18n import gettext as _


@flags.help(exclude=True)
class StartConnectHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CommandStart(deep_link=True, magic=F.args.regexp(r"connect_(-?\d+)")),)

    async def handle(self) -> Any:
        if not self.event.from_user or not self.event.text:
            return

        regex = search(r"connect_(-?\d+)", self.event.text)
        if not regex:
            return

        chat_id = int(regex.group(1))
        user_id = self.event.from_user.id

        # Check permissions
        if not await self.check_permissions(chat_id, user_id):
            return await self.event.reply(_("You are not allowed to connect to this chat."))

        await set_connected_chat(user_id, chat_id)
        chat = await ChatModel.get_by_tid(chat_id)

        text = Doc(
            Title(_("Connected!")),
            Template(_("Connected to {chat_name}."), chat_name=chat.first_name_or_title if chat else str(chat_id)),
            Section(
                _("Notices"),
                _("⚠️ The connection module is obsolete in favor of the web app."),
                _("⏳ This connection will last for 48 hours."),
            ),
        )

        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(CONNECTION_DISCONNECT_TEXT))]], resize_keyboard=True
        )

        await self.event.reply(str(text), reply_markup=markup)

    async def check_permissions(self, chat_id, user_id):
        # Admins always allowed
        if await is_user_admin(chat_id, user_id):
            return True

        # Check settings
        settings = await ChatConnectionSettingsModel.get_by_chat_id(chat_id)
        if settings and not settings.allow_users_connect:
            return False

        return True
