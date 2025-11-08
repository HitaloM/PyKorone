from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import ChatJoinRequest, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sophie_bot.db.models import ChatModel, GreetingsModel
from sophie_bot.modules.greetings.default_welcome import get_default_join_request_message
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.modules.utils_.base_handler import SophieBaseHandler
from sophie_bot.modules.welcomesecurity.utils_.on_new_user import ws_on_new_user
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _


class ChatJoinRequestHandler(SophieBaseHandler[ChatJoinRequest]):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    def register(cls, router):
        router.chat_join_request.register(cls, *cls.filters())

    async def handle(self) -> Any:
        chat_tid = self.event.chat.id
        user_tid = self.event.from_user.id

        # Check if user is admin
        if await is_user_admin(chat_tid, user_tid):
            # Approve immediately
            await self.event.approve()
            return

        # Get chat model
        chat = await ChatModel.get_by_chat_id(chat_tid)
        if not chat:
            return

        # Get greetings model
        greetings = await GreetingsModel.get_by_chat_id(chat_tid)

        # Check if welcomesecurity is enabled
        if not (greetings.welcome_security and greetings.welcome_security.enabled):
            # Approve immediately if not enabled
            await self.event.approve()
            return

        # Get user model
        user = await ChatModel.get_by_chat_id(user_tid)
        if not user:
            return

        # Mute the user (similar to ws_on_new_user)
        muted = await ws_on_new_user(user, chat)
        if not muted:
            await self.event.approve()
            return

        # Send join request message in chat
        join_request_saveable = greetings.join_request_message or get_default_join_request_message()

        # Replace {mention} with user mention
        text = join_request_saveable.text or ""
        text = text.replace("{mention}", self.event.from_user.mention_html())

        # Create button to open DM
        buttons = InlineKeyboardBuilder()
        buttons.add(
            InlineKeyboardButton(text=_("Open DM with Sophie"), url=f"https://t.me/{(await bot.get_me()).username}")
        )

        # Send message in chat
        sent_message = await bot.send_message(chat_id=chat_tid, text=text, reply_markup=buttons.as_markup())

        # Store message ID for cleanup
        from sophie_bot.services.redis import aredis

        await aredis.set(f"join_request_message:{chat.id}:{user.id}", sent_message.message_id)

        # Send captcha to user's DM
        from sophie_bot.modules.welcomesecurity.utils_.captcha_flow import initiate_captcha

        await initiate_captcha(user, chat, greetings, send_to_chat=False)
