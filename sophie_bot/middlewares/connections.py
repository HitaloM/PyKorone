from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

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
    id: int
    title: str
    db_model: Optional[ChatModel]


class ConnectionsMiddleware(BaseMiddleware):
    @staticmethod
    def get_current_chat_info(chat: Chat) -> ChatConnection:
        title = chat.title if chat.type != "private" and chat.title else _("Private chat")
        return ChatConnection(is_connected=False, id=chat.id, type=ChatType[chat.type], title=title, db_model=None)

    @staticmethod
    async def get_chat_from_db(chat_id: int, is_connected: bool) -> ChatConnection:
        chat = await ChatModel.get_by_chat_id(chat_id)

        if not chat:
            raise SophieException(
                _("Connected chat not found in the database. Please try to disconnect and connect again.")
            )

        return ChatConnection(
            is_connected=is_connected, id=chat.chat_id, type=chat.type, title=chat.first_name_or_title, db_model=chat
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
            log.debug("Connections: Non-private chat")
            data["connection"] = self.get_current_chat_info(real_chat)
            return await handler(event, data)

        connection = await ChatConnectionModel.get_by_user_id(real_chat.id)
        if not connection or not connection.chat_id:
            log.debug("Connections: Not connected!")
            data["connection"] = self.get_current_chat_info(real_chat)
            return await handler(event, data)

        log.debug("Connections: connected!")
        data["connection"] = await self.get_chat_from_db(connection.chat_id, True)
        return await handler(event, data)
