from __future__ import annotations

from ass_tg.types import OptionalArg

from aiogram import flags
from aiogram.types import (
    InlineKeyboardButton,
    Message,
)
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from stfu_tg import Doc, Title

from sophie_bot.args.chats import SophieChatArg
from sophie_bot.modules.connections.utils.connection import (
    check_connection_permissions,
    get_connection_text,
    get_disconnect_markup,
    set_connected_chat,
)
from sophie_bot.modules.connections.utils.texts import CONNECTION_OBSOLETE_NOTICE
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.utils.handlers import SophieMessageHandler, SophieCallbackQueryHandler
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter


class ConnectToChatCb(CallbackData, prefix="connect_to_chat_cb"):
    chat_id: int


@flags.help(description=l_("Connects to the chat."))
class ConnectDMCmd(SophieMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict:
        return {"chat": OptionalArg(SophieChatArg(l_("Chat")))}

    @staticmethod
    def filters():
        return CMDFilter("connect"), ChatTypeFilter("private")

    async def handle(self):
        if not self.event.from_user:
            return
        user_id = self.event.from_user.id

        # If chat arg is provided
        if chat_arg := self.data.get("chat"):
            chat_id = chat_arg.tid
            if not await check_connection_permissions(chat_id, user_id):
                await self.event.reply(_("You are not allowed to connect to this chat."))
                return
            await self.do_connect(user_id, chat_id)
            return

        # No arg, show buttons
        conn = await ChatConnectionModel.get_by_user_id(user_id)

        doc = Doc(
            Title(_("Connections")),
            CONNECTION_OBSOLETE_NOTICE,
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
        text = await get_connection_text(chat_id)
        markup = get_disconnect_markup()
        await self.event.reply(str(text), reply_markup=markup)


class ConnectCallback(SophieCallbackQueryHandler):
    @staticmethod
    def filters():
        return (ConnectToChatCb.filter(),)

    async def handle(self):
        user_id = self.event.from_user.id
        chat_id = self.data["callback_data"].chat_id

        # Check permissions
        if not await check_connection_permissions(chat_id, user_id):
            await self.event.answer(_("You are not allowed to connect to this chat."), show_alert=True)
            return

        await set_connected_chat(user_id, chat_id)
        text = await get_connection_text(chat_id)
        markup = get_disconnect_markup()

        if self.event.message:
            await self.event.message.answer(text.to_html(), reply_markup=markup)
