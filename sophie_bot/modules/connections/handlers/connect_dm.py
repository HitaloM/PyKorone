from __future__ import annotations

from aiogram import flags
from aiogram.types import (
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ass_tg.types import IntArg
from stfu_tg import Doc, Title, Template, Section

from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.db.models.chat_connection_settings import ChatConnectionSettingsModel
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler, SophieCallbackQueryHandler
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter


class ConnectToChatCb(CallbackData, prefix="connect_to_chat_cb"):
    chat_id: int


@flags.help(description=l_("Connects to the chat."), args={"chat_id": IntArg(l_("Chat ID"))})
class ConnectDMCmd(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("connect"), ChatTypeFilter("private"))

    async def handle(self):
        if not self.event.from_user:
            return
        user_id = self.event.from_user.id

        # If chat_id arg is provided
        if chat_id := self.data.get("chat_id"):
            if not await self.check_permissions(chat_id, user_id):
                await self.event.reply(_("You are not allowed to connect to this chat."))
                return
            await self.do_connect(user_id, chat_id)
            return

        # No arg, show buttons
        conn = await ChatConnectionModel.get_by_user_id(user_id)

        doc = Doc(
            Title(_("Connections")),
            _("⚠️ The connection module is obsolete in favor of the web app."),
            _("Select a chat to connect to:"),
        )

        buttons = InlineKeyboardBuilder()

        if conn and conn.history:
            # Show last 5
            for h_chat_id in reversed(conn.history[-5:]):
                chat = await ChatModel.get_by_tid(h_chat_id)
                if chat:
                    buttons.add(
                        InlineKeyboardButton(
                            text=chat.first_name_or_title, callback_data=ConnectToChatCb(chat_id=h_chat_id).pack()
                        )
                    )

        buttons.adjust(1)
        await self.event.reply(str(doc), reply_markup=buttons.as_markup())

    async def do_connect(self, user_id: int, chat_id: int):
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

        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/disconnect")]], resize_keyboard=True)

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


class ConnectCallback(SophieCallbackQueryHandler):
    @staticmethod
    def filters():
        return (ConnectToChatCb.filter(),)

    async def handle(self):
        user_id = self.event.from_user.id
        chat_id = self.data["callback_data"].chat_id

        chat = await ChatModel.get_by_tid(chat_id)
        if not chat:
            await self.event.answer(_("Chat not found."), show_alert=True)
            return

        # Check permissions
        if not await is_user_admin(chat_id, user_id):
            settings = await ChatConnectionSettingsModel.get_by_chat_id(chat_id)
            if settings and not settings.allow_users_connect:
                await self.event.answer(_("You are not allowed to connect to this chat."), show_alert=True)
                return

        await set_connected_chat(user_id, chat_id)

        text = Doc(
            Title(_("Connected!")),
            Template(_("Connected to {chat_name}."), chat_name=chat.first_name_or_title),
            Section(
                _("Notices"),
                _("⚠️ The connection module is obsolete in favor of the web app."),
                _("⏳ This connection will last for 48 hours."),
            ),
        )

        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/disconnect")]], resize_keyboard=True)

        await self.edit_text(str(text))
        if self.event.message:
            await self.event.message.answer(_("Keyboard updated."), reply_markup=markup)
