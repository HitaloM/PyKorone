from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message

from korone.config import CONFIG
from korone.modules.ai.utils.cache_messages import cache_message
from korone.modules.ai.utils.self_reply import cut_titlebar, is_ai_message

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject


class CacheBotMessagesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> object:
        result = await handler(event, data)

        chat_db = data.get("chat_db")
        if not chat_db:
            return result

        ai_enabled = bool(data.get("ai_enabled")) or (
            isinstance(event, Message) and event.chat.type == ChatType.PRIVATE
        )
        if not ai_enabled:
            return result

        sent_message_text = result.text if isinstance(result, Message) else None
        if not sent_message_text:
            return result

        if not is_ai_message(sent_message_text):
            return result

        await cache_message(
            cut_titlebar(sent_message_text),
            chat_id=chat_db.chat_id,
            user_id=CONFIG.bot_id,
            role="assistant",
            name="Korone",
        )
        return result
