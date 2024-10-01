from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from pydantic import BaseModel

from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.services.redis import aredis


class MessageType(BaseModel):
    user_id: int
    message_id: int
    text: str


class CacheMessagesMiddleware(BaseMiddleware):
    @staticmethod
    def get_key(chat_id: int | str) -> str:
        return f"messages:{chat_id}"

    async def save_message(self, message: Message):
        if not ((message.text or message.caption) and message.from_user):
            return

        chat_id = message.chat.id

        msg = MessageType(
            user_id=message.from_user.id,
            message_id=message.message_id,
            text=message.text or message.caption or "<No text>",
        )
        json_str = msg.model_dump_json()

        key = self.get_key(message.chat.id)

        await aredis.ltrim(key, -15, -1)  # type: ignore[misc]
        await aredis.expire(key, 86400 * 2, lt=True)  # type: ignore[misc] # 2 days
        await aredis.rpush(self.get_key(chat_id), json_str)  # type: ignore[misc]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_db = data["chat_db"]
        ai_enabled = await AIEnabledFilter.get_status(chat_db)

        result = await handler(event, data)

        if isinstance(event, Message) and ai_enabled:
            await self.save_message(event)

        return result
