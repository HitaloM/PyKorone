from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.cache_messages import cache_message
from sophie_bot.utils.logger import log


class CacheUserMessagesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_db: Optional[ChatModel] = data.get("chat_db", None)

        data["ai_enabled"] = await AIEnabledFilter.get_status(chat_db)  # type: ignore

        result = await handler(event, data)

        if (
            isinstance(event, Message)
            and chat_db
            and event.from_user
            and (data["ai_enabled"] or event.chat.type == "private")
        ):
            text = event.text or event.caption

            # TODO: extract command from handlers? or a flag?
            if text and "/aireset" in text:
                log.debug("CacheUserMessagesMiddleware, skpping due to reset command")
                return result

            user_id = event.from_user.id
            msg_id = event.message_id
            log.debug("CacheUserMessagesMiddleware: caching message", chat_id=chat_db.tid)
            await cache_message(text, chat_db.tid, user_id, msg_id)

        return result
