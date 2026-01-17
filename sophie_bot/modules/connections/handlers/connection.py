from aiogram import Router, flags
from aiogram.types import (
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ass_tg.types import IntArg, BooleanArg
from stfu_tg import Doc, Title, Template, Section

from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.db.models.chat_connection_settings import ChatConnectionSettingsModel
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler, SophieCallbackQueryHandler
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _
from sophie_bot.filters.cmd import CMDFilter

router = Router(name="connection")


class ConnectToChatCb(CallbackData, prefix="connect_to_chat_cb"):
    chat_id: int


@flags.help(description=l_("Connects to the chat by its ID."), args={"chat_id": IntArg(l_("Chat ID"))})
class ConnectCmd(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("connect"),)

    async def handle(self):
        if not self.event.from_user:
            return
        user_id = self.event.from_user.id

        conn = await ChatConnectionModel.get_by_user_id(user_id)

        doc = Doc(
            Title(_("Connections")),
            _("⚠️ The connection module is obsolete in favor of the web app."),
            _("Select a chat to connect to:"),
        )

        buttons = InlineKeyboardBuilder()

        if conn and conn.history:
            # Show last 5
            for chat_id in reversed(conn.history[-5:]):
                chat = await ChatModel.get_by_tid(chat_id)
                if chat:
                    buttons.add(
                        InlineKeyboardButton(
                            text=chat.first_name_or_title, callback_data=ConnectToChatCb(chat_id=chat_id).pack()
                        )
                    )

        buttons.adjust(1)
        await self.event.reply(str(doc), reply_markup=buttons.as_markup())

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
        # Need to instantiate ConnectCmd or move logic.
        # I'll duplicate simple logic or make helper.
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
        # Need to send new message for ReplyMarkup?
        # Yes, can't attach ReplyMarkup to edit_text of bot message usually unless it's a new message.
        # Actually, ReplyMarkup is for user input field. We must send a new message to show it.
        if self.event.message:
            await self.event.message.answer(_("Keyboard updated."), reply_markup=markup)


@flags.help(description=l_("Disconnects from the current chat."))
class DisconnectCmd(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("disconnect"),)

    async def handle(self):
        if not self.event.from_user:
            return

        user_id = self.event.from_user.id
        await set_connected_chat(user_id, None)
        await self.event.reply(_("Disconnected."), reply_markup=ReplyKeyboardRemove())


@flags.help(
    description=l_("Sets whether normal users (non-admins) are allowed to connect."),
    args={"enable": BooleanArg(l_("Enable/Disable"))},
)
class AllowUsersConnectCmd(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("allowusersconnect"),)

    async def handle(self):
        # Must be in group and admin
        if self.event.chat.type == "private":
            await self.event.reply(_("This command can only be used in groups."))
            return

        user_id = self.event.from_user.id if self.event.from_user else 0
        if not await is_user_admin(self.event.chat.id, user_id):
            await self.event.reply(_("You must be an admin to use this command."))
            return

        enable = self.data["enable"]
        chat_id = self.event.chat.id

        settings = await ChatConnectionSettingsModel.get_by_chat_id(chat_id)
        if not settings:
            settings = ChatConnectionSettingsModel(chat_id=chat_id, allow_users_connect=enable)
            await settings.insert()
        else:
            settings.allow_users_connect = enable
            await settings.save()

        status = _("enabled") if enable else _("disabled")
        await self.event.reply(_("Connection for users is now {status}.").format(status=status))
