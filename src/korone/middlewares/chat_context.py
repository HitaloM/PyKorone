from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Chat, TelegramObject

from korone.db.models.chat import ChatModel, ChatType
from korone.logging import get_logger
from korone.utils.i18n import gettext as _

logger = get_logger(__name__)


@dataclass
class ChatContext:
    type: ChatType
    is_connected: bool
    tid: int
    title: str
    db_model: ChatModel


class ChatContextMiddleware(BaseMiddleware):
    @staticmethod
    async def get_current_chat_info(chat: Chat) -> ChatContext:
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

        return ChatContext(is_connected=False, tid=chat.id, type=ChatType[chat.type], title=title, db_model=db_model)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        real_chat: Chat = data["event_chat"]

        await logger.adebug("ChatContextMiddleware: providing current chat info")
        data["chat"] = await self.get_current_chat_info(real_chat)
        return await handler(event, data)
