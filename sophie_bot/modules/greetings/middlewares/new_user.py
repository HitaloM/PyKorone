from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import InlineKeyboardButton, Message, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel, GreetingsModel, RulesModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.modules.greetings.default_welcome import (
    get_default_welcome_message,
    get_default_security_message,
)
from sophie_bot.modules.greetings.utils.send_welcome import send_welcome
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.modules.welcomesecurity.utils_.on_new_user import ws_on_new_users_mute
from sophie_bot.modules.welcomesecurity.utils_.welcomemute import on_welcomemute
from sophie_bot.services.bot import bot
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import gettext as _


class NewUserMiddleware(BaseMiddleware):
    @staticmethod
    async def cleanup(db_item: GreetingsModel, message: Message, sent_message: Optional[Message]) -> GreetingsModel:
        to_delete: list[int] = []

        # Clean service
        if db_item.clean_service and db_item.clean_service.enabled:
            to_delete.append(message.message_id)

        # Clean welcome
        if db_item.clean_welcome and db_item.clean_welcome.enabled:
            if db_item.clean_welcome.last_msg:
                to_delete.append(db_item.clean_welcome.last_msg)

            # Save the new one
            if sent_message:
                db_item = await db_item.clean_welcome_new_message(sent_message.message_id)

        # TODO: Handle exceptions
        if to_delete:
            await common_try(bot.delete_messages(chat_id=message.chat.id, message_ids=to_delete))

        # Save the new one
        return db_item

    @staticmethod
    async def self_welcome(message: Message):
        doc = Doc(
            _("Hi, Thank you for choosing Sophie for your group!"),
            _("Please read the documentation to learn more about Sophie and do not hesitate to join the Support Chat"),
        )

        buttons = InlineKeyboardBuilder()
        buttons.add(
            InlineKeyboardButton(text=_("Documentation"), url=CONFIG.wiki_link),
            InlineKeyboardButton(text=_("Support Chat"), url=CONFIG.support_link),
        )

        return await message.reply(str(doc))

    @staticmethod
    async def is_join_request(chat_id: int, user_id: int) -> bool:
        key = f"chat_ws_message:{chat_id}:{user_id}"
        join_request = await aredis.get(key)
        if join_request:
            await aredis.delete(key)
        return bool(join_request)

    @staticmethod
    async def on_captcha(
        message: Message,
        db_item: GreetingsModel,
        chat_db: ChatModel,
        new_users: list[ChatModel],
        cleanservice_enabled: bool,
        chat_rules: Optional[RulesModel],
    ) -> Optional[Message]:
        muted_users = await ws_on_new_users_mute(new_users, chat_db)

        # If no users were welcomesecurity muted - just send a greetings message
        if not any(muted_users):
            return None

        # If no users were welcomesecurity muted - just send a greetings message
        ws_saveable: Saveable = db_item.security_note or get_default_security_message()

        # FIXME: A workaround to add a missing (btnwelcomesecurity)️ button if not exists
        if "(btnwelcomesecurity)️" not in (ws_saveable.text or ""):
            ws_saveable.text = (ws_saveable.text or "") + f"\n [{_('I am not a robot')}](btnwelcomesecurity)️"

        if not any(muted_users):
            return None

        sent_message = await send_welcome(message, ws_saveable, cleanservice_enabled, chat_rules)
        # Save sent message to cleanup it later
        if len(muted_users) == 1:
            await aredis.set(f"chat_ws_message:{chat_db.id}:{new_users[0].id}", sent_message.message_id)

        return sent_message

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # TODO: Handle multiple users add

        if isinstance(event, Message) and event.new_chat_members:
            if not event.from_user:
                raise ValueError("NewUserMiddleware: 'event.from_user' is None!")

            user_id = event.from_user.id
            chat_id: int = event.chat.id
            chat_db: ChatModel = data["chat_db"]
            new_users: list[ChatModel] = data["new_users"]

            # Bot was added to the chat
            if any(user for user in event.new_chat_members if user.id == CONFIG.bot_id):
                await self.self_welcome(event)
                return await handler(event, data)

            if await self.is_join_request(chat_id, user_id):
                return await handler(event, data)

            # Sanity check
            if tuple(user.id for user in event.new_chat_members) != tuple(user.chat_id for user in new_users):
                raise ValueError("NewUserMiddleware: unexpected / incorrect 'new_users' data from SaveChatsMiddleware!")

            db_item: GreetingsModel = await GreetingsModel.get_by_chat_id(chat_id)

            cleanservice_enabled = bool(db_item.clean_service and db_item.clean_service.enabled)

            is_admin = await is_user_admin(chat_id, user_id)

            # Save sent message to clean it later
            sent_message: Optional[Message] = None

            chat_rules = await RulesModel.get_rules(chat_id)

            # The origin user of the message is admin could indite:
            # 1. Chat owner joined the chat back
            # 2. One of admins added user/users, we do not want to enforce welcomesecurity
            if not (db_item.welcome_disabled or (db_item.welcome_security and db_item.welcome_security.enabled)) or (
                not db_item.welcome_disabled and is_admin
            ):
                welcome_saveable: Saveable = db_item.note or get_default_welcome_message(bool(chat_rules))
                sent_message = await send_welcome(event, welcome_saveable, cleanservice_enabled, chat_rules)

                if db_item.welcome_mute and db_item.welcome_mute.enabled and db_item.welcome_mute.time:
                    await on_welcomemute(chat_id, user_id, db_item.welcome_mute.time)

            elif not is_admin and db_item.welcome_security and db_item.welcome_security.enabled:
                # If group has join_by_request enabled, captcha is handled by join request handler
                # Otherwise, use normal captcha
                if not event.chat.join_by_request:
                    sent_message = await self.on_captcha(
                        event, db_item, chat_db, new_users, cleanservice_enabled, chat_rules
                    )

            # Cleanup
            await self.cleanup(db_item, event, sent_message)

            # Skip handler
            raise SkipHandler

        return await handler(event, data)
