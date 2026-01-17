from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional
from datetime import datetime, timezone

from aiogram import BaseMiddleware
from aiogram.types import Chat, TelegramObject

from sophie_bot.db.models import ChatConnectionModel, ChatModel
from sophie_bot.db.models.chat import ChatType
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
        if not db_model:
            if chat.type == "private":
                db_model = ChatModel(
                    tid=chat.id,
                    type=ChatType.private,
                    first_name_or_title=chat.first_name or "User",
                    last_name=chat.last_name,
                    username=chat.username,
                    is_bot=False,
                    last_saw=datetime.now(timezone.utc),
                )
            else:
                db_model = ChatModel(
                    tid=chat.id,
                    type=ChatType[chat.type],
                    first_name_or_title=chat.title or "Group",
                    is_bot=False,
                    last_saw=datetime.now(timezone.utc),
                )

        return ChatConnection(is_connected=False, tid=chat.id, type=ChatType[chat.type], title=title, db_model=db_model)

    @staticmethod
    async def get_chat_from_db(chat_id: int, is_connected: bool) -> Optional[ChatConnection]:
        chat = await ChatModel.get_by_tid(chat_id)

        if not chat:
            return None

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
        if connection.expires_at:
            expires_at = connection.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                log.debug("ConnectionsMiddleware: Connection expired!")
                connection.chat_id = None
                connection.expires_at = None
                await connection.save()

                data["connection"] = await self.get_current_chat_info(real_chat)
                return await handler(event, data)

        if not (connection_chat := await self.get_chat_from_db(connection.chat_id, True)):
            log.debug("ConnectionsMiddleware: connected, but chat were not found in database, disconnecting...")

            # Disconnect
            connection.chat_id = None
            connection.expires_at = None
            await connection.save()

            # Notify user
            await data["bot"].send_message(
                real_chat.id,
                _("Connected chat not found in the database. You have been disconnected and will remain disconnected."),
            )

            data["connection"] = await self.get_current_chat_info(real_chat)
            return await handler(event, data)

        log.debug("ConnectionsMiddleware: connected!")
        data["connection"] = connection_chat
        return await handler(event, data)
