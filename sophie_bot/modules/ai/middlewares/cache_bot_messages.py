from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject
from pydantic import BaseModel

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.utils.cache_messages import cache_message
from sophie_bot.modules.ai.utils.self_reply import cut_titlebar, is_ai_message
from sophie_bot.utils.logger import log


class MessageType(BaseModel):
    user_id: int
    message_id: int
    text: str


class CacheBotMessagesMiddleware(BaseMiddleware):
    @staticmethod
    def get_key(chat_id: int | str) -> str:
        return f"messages:{chat_id}"

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        result = await handler(event, data)
        chat_db: Optional[ChatModel] = data.get("chat_db", None)

        ai_enabled: bool = data.get("ai_enabled", False) or (
            isinstance(event, Message) and event.chat.type == "private"
        )

        sent_message_text = result.text if isinstance(result, Message) else None
        sent_message_id = result.message_id if isinstance(result, Message) else None

        ai_cache_flag = get_flag(data, "ai_cache", default={})
        cache_handler_result = ai_cache_flag.get("cache_handler_result", False)

        to_cache: Optional[str] = sent_message_text if cache_handler_result else None

        if ai_enabled and to_cache and sent_message_id and chat_db:
            if is_ai_message(to_cache):
                to_cache = cut_titlebar(to_cache)

            log.debug("CacheBotMessagesMiddleware: caching message", message=to_cache)
            await cache_message(to_cache, chat_db.tid, CONFIG.bot_id, sent_message_id)

        return result
