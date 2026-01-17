from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from datetime import datetime, timezone

from aiogram import BaseMiddleware
from aiogram.types import Chat, TelegramObject

from sophie_bot.db.models import ChatConnectionModel, ChatModel
from sophie_bot.db.models.chat import ChatType
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


@dataclass
class ChatConnection:
    type: ChatType
    is_connected: bool
    tid: int
    title: str
    db_model: ChatModel


class ConnectionsMiddleware(BaseMiddleware):
    @staticmethod
    async def get_current_chat_info(chat: Chat) -> ChatConnection:
        title = chat.title if chat.type != "private" and chat.title else _("Private chat")

        db_model = await ChatModel.get_by_tid(chat.id)
        if db_model is None:
            raise SophieException(_("Chat not found in database"))

        return ChatConnection(is_connected=False, tid=chat.id, type=ChatType[chat.type], title=title, db_model=db_model)

    @staticmethod
    async def get_chat_from_db(chat_id: int, is_connected: bool) -> ChatConnection:
        chat = await ChatModel.get_by_tid(chat_id)

        if not chat:
            raise SophieException(
                _("Connected chat not found in the database. Please try to disconnect and connect again.")
            )

        return ChatConnection(
            is_connected=is_connected, tid=chat.tid, type=chat.type, title=chat.first_name_or_title, db_model=chat
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        real_chat: Chat = data["event_chat"]

        # Handle non-private chats
        if real_chat.type != "private":
            log.debug("ConnectionsMiddleware: Non-private chat")
            data["connection"] = await self.get_current_chat_info(real_chat)
            return await handler(event, data)

        connection = await ChatConnectionModel.get_by_user_id(real_chat.id)

        if not connection or not connection.chat_id:
            log.debug("ConnectionsMiddleware: Not connected!")
            data["connection"] = await self.get_current_chat_info(real_chat)
            return await handler(event, data)

        # Check expiry
        if connection.expires_at and connection.expires_at < datetime.now(timezone.utc):
            log.debug("ConnectionsMiddleware: Connection expired!")
            connection.chat_id = None
            connection.expires_at = None
            await connection.save()

            data["connection"] = await self.get_current_chat_info(real_chat)
            return await handler(event, data)

        elif not (connection_chat := await self.get_chat_from_db(connection.chat_id, True)):
            log.debug("ConnectionsMiddleware: connected, but chat were not found in database, skipping...")
            data["connection"] = await self.get_current_chat_info(real_chat)
            return await handler(event, data)

        log.debug("ConnectionsMiddleware: connected!")
        data["connection"] = connection_chat
        return await handler(event, data)
