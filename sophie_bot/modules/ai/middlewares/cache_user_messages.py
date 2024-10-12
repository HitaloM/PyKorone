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

        if isinstance(event, Message) and chat_db and data["ai_enabled"] and event.from_user:
            log.debug("CacheUserMessagesMiddleware: caching message", chat_id=chat_db.chat_id)

            text = event.text or event.caption
            user_id = event.from_user.id
            msg_id = event.message_id
            await cache_message(text, chat_db.chat_id, user_id, msg_id)

        return await handler(event, data)
