from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import TelegramObject

from korone.db.models.chat import ChatModel
from korone.db.repositories import chat as chat_repo
from korone.logging import get_logger
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import Chat

logger = get_logger(__name__)


@dataclass
class ChatContext:
    type: ChatType
    is_connected: bool
    chat_id: int
    title: str
    db_model: ChatModel


type HandlerResult = TelegramObject | bool | None
type MiddlewareDataValue = (
    str
    | int
    | float
    | bool
    | TelegramObject
    | ChatContext
    | ChatModel
    | dict[str, str | int | float | bool | None]
    | None
)
type MiddlewareData = dict[str, MiddlewareDataValue]


class ChatContextMiddleware(BaseMiddleware):
    @staticmethod
    async def get_current_chat_info(chat: Chat) -> ChatContext:
        title = chat.title if chat.type != "private" and chat.title else _("Private chat")

        db_model = await chat_repo.get_by_chat_id(chat.id)
        if not db_model:
            if chat.type == "private":
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
                    type=ChatType[chat.type.upper()],
                    first_name_or_title=chat.title or "Group",
                    is_bot=False,
                    last_saw=datetime.now(UTC),
                )

        chat_type = ChatType.PRIVATE if chat.type == "private" else ChatType[chat.type.upper()]
        return ChatContext(is_connected=False, chat_id=chat.id, type=chat_type, title=title, db_model=db_model)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, MiddlewareData], Awaitable[HandlerResult]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> HandlerResult:
        real_chat = cast("Chat", data["event_chat"])

        await logger.adebug("ChatContextMiddleware: providing current chat info")
        data["chat"] = await self.get_current_chat_info(real_chat)
        return await handler(event, data)
