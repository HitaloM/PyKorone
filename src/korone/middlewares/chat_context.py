from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from aiogram import BaseMiddleware
from aiogram.enums import ChatType

from korone.db.models.chat import ChatModel
from korone.db.repositories.chat import ChatRepository
from korone.logger import get_logger
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import Chat, TelegramObject

logger = get_logger(__name__)


@dataclass
class ChatContext:
    type: ChatType
    chat_id: int
    title: str
    db_model: ChatModel


class ChatContextMiddleware(BaseMiddleware):
    @staticmethod
    async def get_current_chat_info(chat: Chat) -> ChatContext:
        chat_type = ChatType(chat.type)
        title = chat.title if chat_type != ChatType.PRIVATE and chat.title else _("Private chat")

        db_model = await ChatRepository.get_by_chat_id(chat.id)
        if not db_model:
            if chat_type == ChatType.PRIVATE:
                db_model = ChatModel(
                    chat_id=chat.id,
                    type=ChatType.PRIVATE,
                    first_name_or_title=chat.first_name or "User",
                    last_name=chat.last_name,
                    username=chat.username,
                    is_bot=False,
                    last_saw=datetime.now(UTC),
                )
            else:
                db_model = ChatModel(
                    chat_id=chat.id,
                    type=chat_type,
                    first_name_or_title=chat.title or "Group",
                    is_bot=False,
                    last_saw=datetime.now(UTC),
                )

        return ChatContext(type=chat_type, chat_id=chat.id, title=title, db_model=db_model)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        real_chat = cast("Chat", data["event_chat"])

        await logger.adebug("ChatContextMiddleware: providing current chat info")
        data["chat"] = await self.get_current_chat_info(real_chat)
        return await handler(event, data)
