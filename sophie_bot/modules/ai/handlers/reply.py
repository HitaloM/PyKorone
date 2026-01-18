from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message

from sophie_bot.config import CONFIG
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.modules.ai.utils.self_reply import is_ai_message
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.bot import bot


@flags.ai_cache(cache_handler_result=True)
class AiReplyHandler(SophieMessageHandler):
    @staticmethod
    async def filter(message: Message):
        if not message.reply_to_message:
            return False

        if message.reply_to_message.from_user and message.reply_to_message.from_user.id != CONFIG.bot_id:
            return False

        return is_ai_message(message.reply_to_message.text or "")

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return AiReplyHandler.filter, AIThrottleFilter()

    async def handle(self) -> Any:
        await bot.send_chat_action(self.event.chat.id, "typing")
        return await ai_chatbot_reply(self.event, self.connection)
